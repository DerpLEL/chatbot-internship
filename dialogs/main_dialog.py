# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.core import MessageFactory, CardFactory
from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult, ComponentDialog, DialogContext
from botbuilder.dialogs.prompts import (
    OAuthPrompt,
    OAuthPromptSettings,
    ConfirmPrompt,
    PromptOptions,
    TextPrompt,
)
from botbuilder.schema import HeroCard, CardImage
from botbuilder.core import BotFrameworkAdapter
from botbuilder.schema import ActivityTypes

from simple_graph_client import SimpleGraphClient
from .chatbot import *

login = False

class LogoutDialog(ComponentDialog):
    def __init__(self, dialog_id: str, connection_name: str):
        super(LogoutDialog, self).__init__(dialog_id)

        self.connection_name = connection_name
        print(connection_name)

    async def on_begin_dialog(
        self, inner_dc: DialogContext, options: object
    ) -> DialogTurnResult:
        result = await self._interrupt(inner_dc)
        if result:
            return result
        return await super().on_begin_dialog(inner_dc, options)

    async def on_continue_dialog(self, inner_dc: DialogContext) -> DialogTurnResult:
        result = await self._interrupt(inner_dc)
        if result:
            return result
        return await super().on_continue_dialog(inner_dc)

    async def _interrupt(self, inner_dc: DialogContext):
        global login
        if inner_dc.context.activity.type == ActivityTypes.message:
            text = inner_dc.context.activity.text.lower()
            if text == "logout":
                login = False
                bot_adapter: BotFrameworkAdapter = inner_dc.context.adapter
                await bot_adapter.sign_out_user(inner_dc.context, self.connection_name)
                await inner_dc.context.send_activity("Bạn đã đăng xuất thành công.")
                return await inner_dc.cancel_all_dialogs()


class MainDialog(LogoutDialog):
    def __init__(self, connection_name: str):
        self.show_welcome = False

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
            global login

            if step_context.result:
                if login == False:
                    await step_context.context.send_activity("Bạn đã đăng nhập thành công.")
                
                token_response = step_context.result

                # client = SimpleGraphClient(token_response.token)
                # me_info = await client.get_me()
                
                if login == False:
                    login = True

                    token_state = self.bot.test_token((await SimpleGraphClient(token_response.token).get_me())['mail'])
                    if token_state:
                        return await step_context.prompt(
                            TextPrompt.__name__,
                            PromptOptions(
                                prompt=MessageFactory.text(
                                    "Đã lấy được HRM token."
                                )
                            )
                        )

                    return await step_context.prompt(
                        TextPrompt.__name__,
                        PromptOptions(
                            prompt=MessageFactory.text(
                                "Vui lòng nhập HRM token. (Optional)"
                            )
                        ),
                    )

                else:
                    return await step_context.prompt(
                        TextPrompt.__name__,
                        PromptOptions(),
                    )
                    # res = await step_context.prompt(
                    #     TextPrompt.__name__,
                    #     PromptOptions()
                    # )
                    # print("############ Continuing lmao... ############")
            
            await step_context.context.send_activity(
                "Bạn đã đăng nhập thất bại. Vui lòng đăng nhập lại."
            )
            return await step_context.end_dialog()

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
                # client = SimpleGraphClient(token_response.token)
                # me_info = await client.get_me()

                # '**' + me_info['displayName'] + '** ' + 'Đợi tui xíu...'
                await step_context.context.send_activity('...')
                # await step_context.prompt(
                #         TextPrompt.__name__,
                #         PromptOptions(),
                #     )

                # display logged in users name
                if command == "me":      
                    await step_context.context.send_activity(
                        f"You are {(await SimpleGraphClient(token_response.token).get_me())['displayName']}"
                    )

                # display logged in users email
                elif command == "email":
                    await step_context.context.send_activity(
                        f"Your email: {(await SimpleGraphClient(token_response.token).get_me())['mail']}"
                    )
                elif command.lower() == "resetall":
                    cursor.execute(f"""UPDATE history SET chat = N'' WHERE email = '{(await SimpleGraphClient(token_response.token).get_me())['mail']}';""")
                    await step_context.context.send_activity(
                        f"Reset data of user: {(await SimpleGraphClient(token_response.token).get_me())['mail']}"
                    )

                else:
                    reply, doc = self.bot.chat_private(step_context.values["command"], (await SimpleGraphClient(token_response.token).get_me())['mail'], (await SimpleGraphClient(token_response.token).get_me())['displayName'])
                    print("doc: " + str(doc))
                    print("reply:"+ str(reply)) 
                    
                    if type(reply) == str:
                        reply = '**' + (await SimpleGraphClient(token_response.token).get_me())['displayName'] + '** ' + reply
                        await step_context.context.send_activity(reply)

                    else:                 
                        reply['output_text'] = '**' + (await SimpleGraphClient(token_response.token).get_me())['displayName'] + '** ' + reply['output_text']
                        await step_context.context.send_activity(
                            reply['output_text']
                        )

                # await step_context.context.delete_activity(test.id)
        else:
            await step_context.context.send_activity("We couldn't log you in.")

        # await step_context.context.send_activity("Type anything to try again.")
        return await step_context.replace_dialog("WFDialog")
    


