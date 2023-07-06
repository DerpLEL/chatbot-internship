from flask import Flask, render_template, request, jsonify


from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")


app = Flask(__name__)

@app.route("/")
def index():
    return render_template('chat.html')


@app.route("/get", methods=["GET", "POST"])
def chat():
    msg = request.form["msg"]
    
    text1 = '<div>' + msg + '</div>'
    image = """<img src="https://acschatbotnoisintern.blob.core.windows.net/fasf-images/2.3.1.2.step3.png?se=2023-07-06T04%3A17%3A54Z&sp=r&sv=2022-11-02&sr=b&sig=2mhW1K%2B45Id%2Bdlf3fX/aZVY0Ot5jG6exgxVZC6kdV9g%3D" alt="Example Image">"""
    text2 = '<div>' + msg + '</div>'
    print(text1 + text2)
    # Check if any of the form fields are None
    if text1 is None or text2 is None:
        return 'Missing form data'
    # Do something with the text and image data
    return text1 + image + text2


def get_Chat_response(text):

    # Let's chat for 5 lines
    for step in range(5):
        # encode the new user input, add the eos_token and return a tensor in Pytorch
        new_user_input_ids = tokenizer.encode(str(text) + tokenizer.eos_token, return_tensors='pt')

        # append the new user input tokens to the chat history
        bot_input_ids = torch.cat([chat_history_ids, new_user_input_ids], dim=-1) if step > 0 else new_user_input_ids

        # generated a response while limiting the total chat history to 1000 tokens, 
        chat_history_ids = model.generate(bot_input_ids, max_length=1000, pad_token_id=tokenizer.eos_token_id)

        # pretty print last ouput tokens from bot
        return tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)


if __name__ == '__main__':
    app.run()
