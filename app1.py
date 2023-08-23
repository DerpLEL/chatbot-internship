import asyncio  
import sys  
from flask import Flask, request, Response  

from botbuilder.core import (  
    BotFrameworkAdapter,  
    BotFrameworkAdapterSettings,     
    TurnContext,      
)  

from botbuilder.schema import Activity  

from dialogs.echobot import*  

bot = EchoBot()  
  
SETTINGS = BotFrameworkAdapterSettings("b8838874-d6d2-4747-a8c7-862d2f530db0","Gf~8Q~wMv-0j1TwBFlOy4mJauAE2eDKfwwXnTalx")  
ADAPTER = BotFrameworkAdapter(SETTINGS) 

LOOP = asyncio.get_event_loop()  

app = Flask(__name__)

@app.route('/')  
def hello():  
    """Renders a sample page."""  
    return "Hello World!" 



@app.route("/api/messages", methods=["POST"])  
def messages():  
    if "application/json" in request.headers["Content-Type"]:  
        body = request.json  
    else:  
        return Response(status=415)  
  
    activity = Activity().deserialize(body)  
    auth_header = (  
        request.headers["Authorization"] if "Authorization" in request.headers else ""  
    )  
  
    async def aux_func(turn_context):  
        await bot.on_turn(turn_context)  
  
    try:  
        task = LOOP.create_task(  
            ADAPTER.process_activity(activity, auth_header, aux_func)  
        )  
        LOOP.run_until_complete(task)  
        return Response(status=201)  
    except Exception as exception:  
        raise exception  
    
if __name__ == '__main__':  
    import os  
    HOST = os.environ.get('SERVER_HOST', 'localhost')  
    try:  
        PORT = 3978  
    except ValueError:  
        PORT = 5555  
    app.run(HOST, PORT)  