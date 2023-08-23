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
from botbuilder.core import BotFrameworkAdapter, TurnContext
from botbuilder.schema import ActivityTypes, Activity

from simple_graph_client import SimpleGraphClient
from .chatbot import *
import pyodbc
import re
import time
import threading

server = 'sql-chatbot-server.database.windows.net'
database = 'sql-chatbot'
username = 'test-chatbot'
password = 'bMp{]nzt1'
driver = '{ODBC Driver 17 for SQL Server}'

"""
    if Input = "logout"
    logout the chatbot
"""


class LogoutDialog(ComponentDialog):
    def __init__(self, dialog_id: str, connection_name: str):
        super(LogoutDialog, self).__init__(dialog_id)
        self.intent = []
        self.connection_name = connection_name
        # print(connection_name)

    def change_intent(self, value):
        self.intent.append(value)

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
        if inner_dc.context.activity.type == ActivityTypes.message:
            text = inner_dc.context.activity.text.lower()
            if text == "logout":
                bot_adapter: BotFrameworkAdapter = inner_dc.context.adapter
                await bot_adapter.sign_out_user(inner_dc.context, self.connection_name)
                await inner_dc.context.send_activity("Bạn đã đăng xuất thành công.")
                return await inner_dc.cancel_all_dialogs()


"""
    Input: 
        LogoutDialog: class for check command "logout"
    Output:
        output from chatbot and send them to bot
    Purpose:
        make login bot in water fall: prompt_step -> login_step -> command_step -> process_step -> (loop) prompt_step 
"""


class MainDialog(LogoutDialog):
    def __init__(self, connection_name: str):
        self.show_welcome = False
        super(MainDialog, self).__init__(MainDialog.__name__, connection_name)

        self.add_dialog(
            OAuthPrompt(
                OAuthPrompt.__name__,
                OAuthPromptSettings(
                    connection_name=connection_name,
                    text="Vui lòng đăng nhập",
                    title="Đăng nhập",
                    timeout=30000,
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
                    # self.command_step,
                    # self.process_step,
                ],
            )
        )

        self.initial_dialog_id = "WFDialog"
        self.bot = chatAI()
        self.bot.private = True

    async def prompt_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        return await step_context.begin_dialog(OAuthPrompt.__name__)

    async def login_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if step_context.result:
            token_response = step_context.result
            client = SimpleGraphClient(token_response.token)
            try:
                if (await client.get_me())['displayName'] and step_context.context.activity.text:
                    print(step_context.context.activity.text)
                    typing_activity = Activity(type=ActivityTypes.typing)
                    await step_context.context.send_activity(typing_activity)

                    if step_context.context.activity.text == "me":
                        await step_context.context.send_activity(
                            f"You are {(await client.get_me())['displayName']}"
                        )
                        # display logged in users email
                    elif step_context.context.activity.text == "email":
                        await step_context.context.send_activity(
                            f"Your email: {(await client.get_me())['mail']}"
                        )
                    elif step_context.context.activity.text.lower().strip() == "resetall":
                        conn = pyodbc.connect(
                            f'DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}')
                        cursor = conn.cursor()

                        cursor.execute(f"""UPDATE history SET chat = N'', 
                        post_leave = N'',
                        del_leave = N'',
                        conversation_type = N'',
                        token = N'',
                        confirm_check = N'',
                        leave_type = N'',
                        confirm_delete = N''
                        WHERE email = '{(await SimpleGraphClient(token_response.token).get_me())['mail']}';""")
                        conn.commit()

                        conn.close()



                    else:
                        try:
                            await step_context.context.send_activity('**' + (await client.get_me())['displayName'] + '** ' + self.bot.chat(step_context.context.activity.text, (await client.get_me())['mail'], (await client.get_me())['displayName'])[0]['output_text'])
                            return await step_context.end_dialog()
                        except:
                            await step_context.context.send_activity('**' + (await client.get_me())['displayName'] + '** ' + self.bot.chat(step_context.context.activity.text, (await client.get_me())['mail'], (await client.get_me())['displayName'])[0])
                            return await step_context.end_dialog()
                            # reply, doc =

                            # if type(reply) == str:
                            #     reply = '**' + me_info['displayName'] + '** ' + reply
                            #     await step_context.context.send_activity(reply)
                            # else:
                            #     reply['output_text'] = '**' + me_info['displayName'] + '** ' + reply['output_text']
                            #     await step_context.context.send_activity(
                            #         reply['output_text'])

                    # print(step_context.values["command"] = step_context.result)

            except:
                conn = pyodbc.connect(
                    f'DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}')
                cursor = conn.cursor()

                cursor.execute(f"""UPDATE history SET chat = N'', 
                post_leave = N'',
                del_leave = N'',
                conversation_type = N'',
                token = N'',
                confirm_check = N'',
                leave_type = N'',
                confirm_delete = N''
                WHERE email = '{(await SimpleGraphClient(token_response.token).get_me())['mail']}';""")
                conn.commit()

                conn.close()

            return await step_context.end_dialog()
            # return await step_context.next(None)

        await step_context.context.send_activity(
            "Bạn đã đăng nhập thất bại. Vui lòng đăng nhập lại."
        )
        return await step_context.end_dialog()

    async def command_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        print(step_context.result)
        step_context.values["command"] = step_context.result
        print(step_context.values["command"])

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
        print(4)
        if step_context.result:
            token_response = step_context.result
            if token_response and token_response.token:
                command = step_context.values["command"]
                command = re.sub('<at>.*?</at>', '', command)
                # print(command)

                client = SimpleGraphClient(token_response.token)
                me_info = await client.get_me()

                # '**' + me_info['displayName'] + '** ' + 'Đợi tui xíu...'
                # test = await step_context.context.send_activity('**' + me_info['displayName'] + '** ' + 'Đợi tui xíu...')

                typing_activity = Activity(type=ActivityTypes.typing)
                await step_context.context.send_activity(typing_activity)

                if command == "me":
                    await step_context.context.send_activity(
                        f"You are {me_info['a']}"
                    )

                # display logged in users email
                elif command == "email":
                    await step_context.context.send_activity(
                        f"Your email: {me_info['mail']}"
                    )
                elif command.lower().strip() == "resetall":
                    conn = pyodbc.connect(
                        f'DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}')
                    cursor = conn.cursor()

                    cursor.execute(f"""UPDATE history SET chat = N'', 
                    post_leave = N'',
                    del_leave = N'',
                    conversation_type = N'',
                    token = N'',
                    confirm_check = N'',
                    leave_type = N'',
                    confirm_delete = N''
                    WHERE email = '{(await SimpleGraphClient(token_response.token).get_me())['mail']}';""")
                    conn.commit()

                    conn.close()

                    await step_context.context.send_activity(
                        f"Reset data of user: {me_info['mail']}"
                    )

                else:
                    try:
                        # reply, doc = self.bot.chat(
                        #     step_context.values["command"], me_info['mail'], me_info['displayName'])

                        if type(reply) == str:
                            reply = '**' + \
                                me_info['displayName'] + '** ' + reply
                            await step_context.context.send_activity(reply)
                        else:
                            reply['output_text'] = '**' + \
                                me_info['displayName'] + \
                                '** ' + reply['output_text']
                            await step_context.context.send_activity(
                                reply['output_text']
                            )
                    except Exception as e:
                        conn = pyodbc.connect(
                            f'DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}')
                        cursor = conn.cursor()
                        cursor.execute(f"""DELETE FROM history WHERE email = '{(await SimpleGraphClient(token_response.token).get_me())['mail']}';""")
                        conn.commit()

                        conn.close()

                        await step_context.context.send_activity(
                            """Hiện tại hệ thống đang gặp một chút vấn đề. :(("""
                        )
                        await step_context.context.send_activity(
                            """Bạn có thể gửi tin nhắn vừa rồi sau một vài giây được không?"""
                        )
                        print("error:", e)
                        pass

        else:
            await step_context.context.send_activity("We couldn't log you in.")

        # return await step_context.replace_dialog("WFDialog")
        return await step_context.end_dialog()
