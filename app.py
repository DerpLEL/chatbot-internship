from flask import Flask, render_template, request, jsonify
from chatbot import *
import threading

agent_session = False

bot = chatAI()

app = Flask(__name__)

user_msg = ""

bot_message = ""

# Toggle agent upon startup
bot.toggle_agent1()

@app.route("/")
def index():
    return render_template('chat.html')


def get_bot_response():
    while not bot.agent.msg.output:
        pass

    msg = bot.agent.msg.output
    bot.agent.msg.reset()

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
        agent_arg = 1
        agent_type = bot.choose_agent(msg).strip()

        if agent_type == "subdel":
            agent_arg = 2

        t1 = threading.Thread(target=run_agent, args=(msg,agent_arg,), daemon=True)
        t1.start()

        new_msg = get_bot_response()

        return new_msg

    # Maintain agent conversation, as long as agent_session is true
    if agent_session:
        print(f"Still in agent session, current user message: {msg}")
        bot.agent.msg.input = msg

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


def run_agent(query, agent_type):
    global agent_session
    if agent_type == 1:
        print("Running agent 1...")
        bot.agent.run1(query)

    else:
        print("Running agent 2...")
        bot.agent.run2(query)

    agent_session = False
    return


if __name__ == '__main__':
    app.run(port=8000)
