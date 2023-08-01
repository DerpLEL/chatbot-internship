# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.core import MessageFactory, CardFactory
from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.dialogs.prompts import (
    OAuthPrompt,
    OAuthPromptSettings,
    ConfirmPrompt,
    PromptOptions,
    TextPrompt,
)
from botbuilder.schema import HeroCard, CardImage

from dialogs import LogoutDialog
from simple_graph_client import SimpleGraphClient
from .chatbot import *


class MainDialog(LogoutDialog):
    login = False

    def __init__(self, connection_name: str):
        super(MainDialog, self).__init__(MainDialog.__name__, connection_name)

        self.add_dialog(
            OAuthPrompt(
                OAuthPrompt.__name__,
                OAuthPromptSettings(
                    connection_name=connection_name,
                    text="Please Sign In",
                    title="Sign In",
                    timeout=300000,
                ),
            )
        )

        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))

        self.add_dialog(
            WaterfallDialog(
                "WFDialog",
                [
                    self.prompt_step,
                    self.login_step,
                    self.command_step,
                    self.process_step,
                ],
            )
        )

        self.initial_dialog_id = "WFDialog"
        self.bot = chatAI()
        self.bot.private = True

    async def prompt_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        return await step_context.begin_dialog(OAuthPrompt.__name__)

    async def login_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # Get the token from the previous step. Note that we could also have gotten the
        # token directly from the prompt itself. There is an example of this in the next method.
        # print(self.login)
        # if self.login == False:
            if step_context.result:
                self.login = True
                if self.login == False:
                    await step_context.context.send_activity("Bạn đã đăng nhập thành công.")

                # token_response = step_context.result
                # client = SimpleGraphClient(token_response.token)
                # me_info = await client.get_me()
                # self.bot.user['username'] = me_info['displayName']
                # self.bot.user['mail'] = me_info['mail']
                
                if self.login == False:
                    return await step_context.prompt(
                        TextPrompt.__name__,
                        PromptOptions(
                            prompt=MessageFactory.text(
                                "Bạn có cần tôi giúp gì không?"
                            )
                        ),
                    )
                else:
                    return await step_context.prompt(
                        TextPrompt.__name__,
                        PromptOptions(
                            prompt=MessageFactory.text(
                                "Bạn đợi 1 xíu ..."
                            )
                        ),
                    )
            

            await step_context.context.send_activity(
                "Bạn đã đăng nhập thất bại. Vui lòng đăng nhập lại."
            )
            return await step_context.end_dialog()
        # return await step_context.next(None)

    async def command_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        step_context.values["command"] = step_context.result

        # Call the prompt again because we need the token. The reasons for this are:
        # 1. If the user is already logged in we do not need to store the token locally in the bot and worry
        #    about refreshing it. We can always just call the prompt again to get the token.
        # 2. We never know how long it will take a user to respond. By the time the
        #    user responds the token may have expired. The user would then be prompted to login again.
        #
        # There is no reason to store the token locally in the bot because we can always just call
        # the OAuth prompt to get the token or get a new token if needed.
        return await step_context.begin_dialog(OAuthPrompt.__name__)

    async def process_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        if step_context.result:
            token_response = step_context.result
            if token_response and token_response.token:
                # print(f'{step_context.values["command"] = }')
                parts = step_context.values["command"].split(" ")
                command = parts[0]

                # display logged in users name
                if command == "me":
                    client = SimpleGraphClient(token_response.token)
                    me_info = await client.get_me()
                    await step_context.context.send_activity(
                        f"You are {me_info['displayName']}"
                    )

                # display logged in users email
                elif command == "email":
                    client = SimpleGraphClient(token_response.token)
                    me_info = await client.get_me()
                    await step_context.context.send_activity(
                        f"Your email: {me_info['mail']}"
                    )

                elif command == "agent":
                    client = SimpleGraphClient(token_response.token)
                    me_info = await client.get_me()
                    await step_context.context.send_activity(
                        self.bot.toggle_agent(me_info['mail'])
                    )

                elif email in self.bot.agent_session and self.bot.agent_session[email][0] and \
                not self.bot.agent_session[email][1]:
                    msg = step_context.values["command"]
                    agent_arg = 1
                    agent_type = self.bot.choose_agent(msg).strip()

                    if agent_type == "subdel":
                        agent_arg = 2

                    t1 = threading.Thread(target=run_agent, args=(msg, agent_arg,), daemon=True)
                    t1.start()

                    new_msg = get_bot_response(self)

                    return new_msg

                elif email in self.bot.agent_session and self.bot.agent_session[email][1]:
                    msg = step_context.values['command']
                    print(f"Still in agent session, current user message: {msg}")
                    self.bot.agent.msg.input = msg

                    new_msg = get_bot_response(self)

                    return new_msg

                else:
                    client = SimpleGraphClient(token_response.token)
                    me_info = await client.get_me()

                    reply, doc = self.bot.chat(step_context.values["command"], me_info['mail'], me_info['displayName'])

                    print("doc: " + str(doc))
                    print("reply:" + str(reply))

                    if type(reply) == str:
                        await step_context.context.send_activity(reply)
                    else:                        
                        await step_context.context.send_activity(
                            reply['output_text']
                        )
        else:
            await step_context.context.send_activity("We couldn't log you in.")

        # await step_context.context.send_activity("Type anything to try again.")
        return await step_context.replace_dialog("WFDialog")


def run_agent(obj: MainDialog, query, email, agent_type):
    obj.bot.agent_session[email][1] = True
    if agent_type == 1:
        print("Running agent 1...")
        obj.bot.agent.run1(query)

    else:
        print("Running agent 2...")
        obj.bot.agent.run2(query)

    obj.bot.agent_session[email][1] = False
    return


def get_bot_response(obj: MainDialog):
    while not obj.bot.agent.msg.output:
        pass

    msg = obj.bot.agent.msg.output
    obj.bot.agent.msg.reset()

    return msg
