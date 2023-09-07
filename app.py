# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import sys
import traceback
from datetime import datetime
from http import HTTPStatus
import jsonpickle
import pyodbc
import requests
import base64
import pprint

from aiohttp import web
from flask import Flask, request, Response, render_template
from aiohttp.web import Request, Response, json_response
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    ConversationState,
    MemoryStorage,
    TurnContext,
    UserState,
    ShowTypingMiddleware,
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity, ActivityTypes
import jwt

from bots import AuthBot

# Create the loop and Flask app
from config import DefaultConfig
from dialogs import MainDialog

import asyncio
import threading
import time
import nest_asyncio

nest_asyncio.apply()

CONFIG = DefaultConfig()

# Create adapter.
# See https://aka.ms/about-bot-adapter to learn more about how bots work.
SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID, CONFIG.APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)
ADAPTER.use(ShowTypingMiddleware(0.1, 0.5))

LOOP = asyncio.get_event_loop()

# Catch-all for errors.


async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("Hiện tại hệ thống đang gặp một chút vấn đề. :((")
    await context.send_activity(
        "Bạn có thể gửi tin nhắn vừa rồi sau một vài giây được không."
    )

    # Send a trace activity if we're talking to the Bot Framework Emulator
    if context.activity.channel_id == "emulator":
        # Create a trace activity that contains the error object
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.utcnow(),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
        )
        # Send a trace activity, which will be displayed in Bot Framework Emulator
        await context.send_activity(trace_activity)


ADAPTER.on_turn_error = on_error

# Create MemoryStorage and state
MEMORY = MemoryStorage()
USER_STATE = UserState(MEMORY)
CONVERSATION_STATE = ConversationState(MEMORY)

# Create dialog
DIALOG = MainDialog(CONFIG.CONNECTION_NAME)

# Create Bot
BOT = AuthBot(CONVERSATION_STATE, USER_STATE, DIALOG)


# Listen for incoming requests on /api/messages.
#  fix this part lmao

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('chat.html')


@app.route("/api/messages", methods=["POST"])
async def messages():
    if "application/json" in request.headers["Content-Type"]:
        body = request.json
        # print("Body:", body)
    else:
        return jsonpickle.encode(Response(status=415))

    activity = Activity().deserialize(body)
    # print("Activity:", activity)

    auth_header = request.headers["Authorization"] if "Authorization" in request.headers else ""

    # print(await ADAPTER.process_activity(activity, auth_header, BOT.on_turn))
    try:
        # async def worker():
        #     await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
        #     task = LOOP.create_task(ADAPTER.process_activity(activity, auth_header, BOT.on_turn))
        #     LOOP.run_until_complete(task)

        # def run_worker():
        #     asyncio.run(worker())

        # thread = threading.Thread(target=run_worker, daemon=True)
        # thread.start()

        # task = LOOP.create_task(aux_func())

        # Run the event loop until all tasks are compxleted
        # await asyncio.wait_for(task, timeout=5)

        # async def run_session():
        #     async def aux_func(turn_context):
        #         DIALOG.change_intent(turn_context.activity.text)

        #     tasks = [
        #         # asyncio.create_task(ADAPTER.process_activity(activity, auth_header, aux_func)),
        #         asyncio.create_task(ADAPTER.process_activity(activity, auth_header, BOT.on_turn)),
        #     ]

        #     # await asyncio.gather(*tasks)
        #     await asyncio.wait(tasks)
        # await asyncio.run(asyncio.gather(*tasks))

        # asyncio.run(run_session())

        # # await ADAPTER.process_activity(activity, auth_header, aux_func)
        # # await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)

        # async def worker():
        #     await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)

        # def run_worker():
        #     asyncio.run(worker())

        # thread = threading.Thread(target=run_worker, daemon=False)
        # thread.start()

        async def worker():
            start_time = time.time()
            await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
            end_time = time.time()
            print(end_time - start_time)
            if end_time - start_time < 0.5:
                await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)

        async def run_session():
            task = asyncio.ensure_future(worker())
            # await asyncio.ensure_future(task)
            # await asyncio.wait_for(task)
            # await task
            await task

        # asyncio.run(run_session())
        thread = threading.Thread(
            target=asyncio.run(run_session()), daemon=False)
        thread.start()
        thread.join()

        #     # async def aux_func(turn_context):
        #     #     DIALOG.change_intent(turn_context.activity.text)
        #     # await ADAPTER.process_activity(activity, auth_header, aux_func)
        #     await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)

        # task = LOOP.create_task(run_session())
        # LOOP.run_until_complete(task)

        return jsonpickle.encode(Response(status=201))
    except Exception as exception:
        raise exception

@app.route("/graph_token", methods=["GET"])
def update_graph_token():
    args = request.args
    code = args.get("code")
    mail = args.get("state")

    print("Code:", code)
    print("Target mail:", mail)

    # Get token here
    endpoint = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    header = {
        'Content-type': 'application/x-www-form-urlencoded'
    }

    string = f"api://botid-b8838874-d6d2-4747-a8c7-862d2f530db0/meetings2"
    string2 = "Calendars.ReadWrite OnlineMeetings.Read OnlineMeetings.ReadWrite"

    body = {
        'grant_type': 'authorization_code',
        'client_id': "b8838874-d6d2-4747-a8c7-862d2f530db0",
        'client_secret': "Gf~8Q~wMv-0j1TwBFlOy4mJauAE2eDKfwwXnTalx",
        'scope': string2,
        'redirect_uri': 'http://localhost:3978/graph_token',
        'code': code,
    }

    x = requests.post(
        "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        headers=header,
        data=body
    )

    print(x.status_code)
    pprint.pprint(x.json())
    body = x.json()
    token = body['access_token']

    return f"""Target user: {mail}
Token: {token}"""

    # server = 'sql-chatbot-server.database.windows.net'
    # database = 'sql-chatbot'
    # username = 'test-chatbot'
    # password = 'bMp{]nzt1'
    # driver = '{ODBC Driver 17 for SQL Server}'
    #
    # conn = pyodbc.connect(f'DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}')
    # cursor = conn.cursor()

#     return f"""Authorization complete for Graph API, please input your meeting query again when you return to the chat interface.
# You can close this window."""

if __name__ == '__main__':
    import os
    HOST = 'localhost'
    try:
        PORT = 3978
    except ValueError:
        PORT = 5555
    app.run(debug=False, threaded=True, host="0.0.0.0", port=CONFIG.PORT)
