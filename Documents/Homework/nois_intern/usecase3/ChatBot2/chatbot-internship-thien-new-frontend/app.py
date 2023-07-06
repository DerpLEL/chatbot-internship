from flask import Flask, render_template, request, jsonify

from PIL import Image
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# image processing
from PIL import Image
import urllib.request
import io

# tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
# model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")


app = Flask(__name__)

@app.route("/")
def index():
    return render_template('chat.html')



    
@app.route("/get", methods=["GET", "POST"])
def chat():
    msg = request.form["msg"]
    
    text1 = '<div>' + msg + '</div>'
    text2 = '<div>' + msg + '</div>'


    # image size self-modification
    # set URL here
    URL = 'https://acschatbotnoisintern.blob.core.windows.net/fasf-images/2.3.1.2.step3.png?se=2023-07-06T07%3A29%3A12Z&sp=r&sv=2022-11-02&sr=b&sig=wftdW/nzMfDHOrUSqAkmKhVIDCegIEKOswKwwO7Ah30%3D'

    with urllib.request.urlopen(URL) as url:
        f = io.BytesIO(url.read())

    img = Image.open(f)

    # Get the size of the image
    w, h = img.size

    # if wanted to adjust the sized wanted to limit change here
    if w > 500 and h >500:
        w /= 2
        h /= 2 

    
    image_html = f'<img src="{URL}" alt="Example Image" style="width: {w}px; height: {h}px;">'
    # Check if any of the form fields are None
    if text1 is None or text2 is None:
        return 'Missing form data'
    # Do something with the text and image data
    return text1 + image_html + text2


def get_Chat_response(text):

    # Let's chat for 5 lines
    # for step in range(5):
    #     # encode the new user input, add the eos_token and return a tensor in Pytorch
    #     new_user_input_ids = tokenizer.encode(str(text) + tokenizer.eos_token, return_tensors='pt')

    #     # append the new user input tokens to the chat history
    #     bot_input_ids = torch.cat([chat_history_ids, new_user_input_ids], dim=-1) if step > 0 else new_user_input_ids

    #     # generated a response while limiting the total chat history to 1000 tokens, 
    #     chat_history_ids = model.generate(bot_input_ids, max_length=1000, pad_token_id=tokenizer.eos_token_id)

    #     # pretty print last ouput tokens from bot
    #     return tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)

    return
if __name__ == '__main__':
    app.run()
