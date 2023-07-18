from flask import Flask, render_template, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
from chatbot import *
import torch
import threading

agent_session = False

bot = chatAI()

app = Flask(__name__)

hist = ""

bot_message = ""

@app.route("/")
def index():
    return render_template('chat.html')


@app.route("/get", methods=["GET", "POST"])
async def chat():
    global agent_session
    global bot_message
    msg = request.form["msg"]

    if msg.strip().lower() == "agent":
        return bot.toggle_agent()

    # Kickstart agent conversation
    if bot.use_agent and not agent_session:
        agent_session = True
        t1 = threading.Thread(target=run_agent, args=(msg,), daemon=True)
        t1.start()

        while not bot_message:
            pass

        new_msg = bot_message.split(":")[1]
        bot_message = ""

        return new_msg

    # Maintain agent conversation, as long as agent_session is true
    if agent_session:
        while not bot_message:
            pass

        new_msg = bot_message.split(":")[1]
        bot_message = ""

        return new_msg

    # if msg.startswith("agent_msg"):
    #     new_msg = msg.split(":")[1]
    #     return msg

    response = bot.chat(msg)
    
    # text1 = '<div>' + msg + '</div>'
    # image = """<img src="https://acschatbotnoisintern.blob.core.windows.net/fasf-images/2.3.1.2.step3.png?se=2023-07-06T04%3A17%3A54Z&sp=r&sv=2022-11-02&sr=b&sig=2mhW1K%2B45Id%2Bdlf3fX/aZVY0Ot5jG6exgxVZC6kdV9g%3D" alt="Example Image">"""
    # text2 = '<div>' + msg + '</div>'
    # print(text1 + text2)
    # # Check if any of the form fields are None
    # if text1 is None or text2 is None:
    #     return 'Missing form data'
    # # Do something with the text and image data
    # return text1 + image + text2

    return response


def run_agent(query):
    bot.agent.run1(query)

    global agent_session
    agent_session = False
    return


@app.route("/agent", methods=["POST"])
def get_message_agent():
    msg = request.form["msg"]
    global bot_message
    bot_message = msg

    return jsonify({"message": "OK"})


if __name__ == '__main__':
    app.run()
