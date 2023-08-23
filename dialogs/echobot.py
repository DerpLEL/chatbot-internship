from sys import exit  
from .chatbot import *
  
class EchoBot:
    def __init__(self):
        self.bot = chatAI()

    async def on_turn(self, context):  
        if context.activity.type == "message" and context.activity.text:  
            # strlen = len(context.activity.text)  
            # sendInfo = "Hey you send text : " + context.activity.text + "  and  the lenght of the string is  " + str(strlen)  
            
            return context.activity.text
    def chat(self, message):
        reply, doc = self.bot.chat(message, 'customer@nois.vn', 'customer')
        if type(reply) == str:
            return reply
        else:
            return reply['output_text']