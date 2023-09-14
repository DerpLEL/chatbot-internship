# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import datetime

import requests
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
                if (await client.get_me())['displayName'] and re.sub('<at>.*?</at>', '', step_context.context.activity.text):
                    print(re.sub('<at>.*?</at>', '',
                          step_context.context.activity.text))
                    typing_activity = Activity(type=ActivityTypes.typing)
                    await step_context.context.send_activity(typing_activity)

                    if re.sub('<at>.*?</at>', '', step_context.context.activity.text) == "me":
                        await step_context.context.send_activity(
                            '**' + (await client.get_me())['displayName'] + '** ' + f"You are {(await client.get_me())['displayName']}"
                        )
                        # display logged in users email

                    elif re.sub('<at>.*?</at>', '', step_context.context.activity.text) == "email":
                        await step_context.context.send_activity(
                            '**' + (await client.get_me())['displayName'] + '** ' + f"Your email: {(await client.get_me())['mail']}"
                        )

                    elif re.sub('<at>.*?</at>', '', step_context.context.activity.text) == "debug":
                        await step_context.context.send_activity(
                            await client.get_me()
                        )

                    elif re.sub('<at>.*?</at>', '', step_context.context.activity.text).lower().strip() == "resetall":
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
                            '**' + (await client.get_me())['displayName'] + '** ' + f"Reset all data: {(await client.get_me())['mail']}"
                        )

                    elif re.sub('<at>.*?</at>', '', step_context.context.activity.text).lower().strip() == "token":
                        await step_context.context.send_activity(
                            '**' + (await client.get_me())['displayName'] + '** ' +
                            token_response.token
                        )

                    else:
                        await step_context.context.send_activity('**' + (await client.get_me())['displayName'] + '** ' + self.bot.chat(re.sub('<at>.*?</at>', '', step_context.context.activity.text), await client.get_me(), token_response.token)[0])
                        # try:
                        #     await step_context.context.send_activity('**' + (await client.get_me())['displayName'] + '** ' + self.bot.chat(re.sub('<at>.*?</at>', '', step_context.context.activity.text), (await client.get_me())['mail'], (await client.get_me())['displayName'])[0]['output_text'])
                        # except:
                        #     await step_context.context.send_activity('**' + (await client.get_me())['displayName'] + '** ' + self.bot.chat(re.sub('<at>.*?</at>', '', step_context.context.activity.text), (await client.get_me())['mail'], (await client.get_me())['displayName'])[0])

            except Exception as e:
                print("Error:", e)

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

        await step_context.context.send_activity(
            "Bạn đã đăng nhập thất bại. Vui lòng đăng nhập lại."
        )
        return await step_context.end_dialog()
