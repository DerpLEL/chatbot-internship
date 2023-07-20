from flask import Flask, render_template, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
from chatbot import *
import torch
import threading

agent_session = False

bot = chatAI()

app = Flask(__name__)

user_msg = ""

bot_message = ""

@app.route("/")
def index():
    return render_template('chat.html')


def get_bot_response():
    global bot_message

    while not bot_message:
        pass

    msg = bot_message
    bot_message = ""

    return msg


@app.route("/get", methods=["GET", "POST"])
def chat():
    global agent_session
    global user_msg
    msg = request.form["msg"]

    if msg.strip().lower() == "agent":
        return bot.toggle_agent1()

    elif msg.strip().lower() == "hist":
        return bot.clear_agent_history()

    # Kickstart agent conversation
    if bot.use_agent and not agent_session:
        agent_session = True
        t1 = threading.Thread(target=run_agent, args=(msg,), daemon=True)
        t1.start()

        # while not bot_message:
        #     pass
        #
        # new_msg = bot_message.split(":")[1]
        # bot_message = ""

        new_msg = get_bot_response()

        return new_msg

    # Maintain agent conversation, as long as agent_session is true
    if agent_session:
        print(f"Still in agent session, current user message: {msg}")
        user_msg = msg

        # while not bot_message:
        #     pass
        #
        # new_msg = bot_message.split(":")[1]
        # bot_message = ""

        new_msg = get_bot_response()

        return new_msg

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
    global agent_session
    bot.agent.run1(query)

    agent_session = False
    return


@app.route("/agent", methods=["POST"])
def get_message_agent():
    msg = request.form["msg"]
    global bot_message
    bot_message = msg

    return jsonify({"msg": "OK"})

@app.route("/user", methods=["GET"])
def get_message_user():
    global user_msg
    msg = user_msg
    user_msg = ""

    return jsonify({"msg": msg})


if __name__ == '__main__':
    app.run()
