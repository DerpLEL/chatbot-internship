import os
import wave
import pyaudio
from flask import Flask, render_template, request, jsonify

from chat import get_response

from langchain.llms import AzureOpenAI
from langchain.retrievers import AzureCognitiveSearchRetriever
from langchain.prompts import PromptTemplate
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
import os

os.environ['OPENAI_API_TYPE'] = 'azure'
os.environ['OPENAI_API_VERSION'] = '2023-03-15-preview'
os.environ['OPENAI_API_BASE'] = 'https://openai-nois-intern.openai.azure.com/'
os.environ['OPENAI_API_KEY'] = '400568d9a16740b88aff437480544a39'

index_type = 'public-index-ver2'

os.environ["AZURE_COGNITIVE_SEARCH_SERVICE_NAME"] = "search-service01"
os.environ["AZURE_COGNITIVE_SEARCH_INDEX_NAME"] = index_type
os.environ["AZURE_COGNITIVE_SEARCH_API_KEY"] = "73Swa5YqUR5IRMwUIqOH6ww2YBm3SveLv7rDmZVXtIAzSeBjEQe9"

app = Flask(__name__)


llm = AzureOpenAI(
deployment_name="text-davinci-003",
model_name="text-davinci-003",
max_tokens=512,
temperature=0.5
)


template = """You have to search for data in both by VietNamese and by English. Input data in any language will output that language.
If the user greets you, respond accordingly.
If you don't know the answer, just say that you don't know. Don't try to make up an answer. DON'T use other sources than the ones provided.
When asked a question not related to the documents, say "Sorry, I will only answer questions related to New Ocean. Could you please ask another related question?"
------
{summaries}
------
QUESTION: {question}
FINAL ANSWER:"""


templ = PromptTemplate(
input_variables=['summaries', 'question'],
output_parser=None,
partial_variables={},
template=template,
template_format='f-string',
validate_template=True
)


qaChain = load_qa_with_sources_chain(llm=llm, chain_type="stuff", prompt=templ)



retriever = AzureCognitiveSearchRetriever(content_key='content')

def getDocuments(query):
    doc = retriever.get_relevant_documents(query)[:3]

    if isinstance(doc, list):
        num = 1
        for x in doc:
            x.metadata['source'] = f"doc-{num}"

            num += 1

    else:
        doc.metadata['source'] = "doc-1"
        doc = [doc]

    return doc

app = Flask(__name__)

history = ' '

@app.get("/")
def index_get():
    return render_template("base.html")

@app.post("/predict")
def predict():
    
    text = request.get_json().get("message")
    raise Exception(type(text))
    doc = getDocuments(text) 

    response = qaChain({'input_documents': doc, 'question': text}, return_only_outputs=True)

    # response = get_response(text)

    message = {"answer": response['output_text']}

    history += response['output_text']

    return jsonify(message)


if __name__ == "__main__":
    app.run(debug = True)
