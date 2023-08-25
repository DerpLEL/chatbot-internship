from langchain.prompts import PromptTemplate
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import LLMChain
from langchain.agents.agent_toolkits.openapi import planner
from langchain.schema import Document
import requests


llm2 = AzureChatOpenAI(
    openai_api_type="azure",
    openai_api_base='https://openai-nois-intern.openai.azure.com/',
    openai_api_version="2023-03-15-preview",
    deployment_name='gpt-35-turbo-16k',
    openai_api_key='400568d9a16740b88aff437480544a39',
    temperature=0.7,
    max_tokens=600
)

# for keyword -later on
llm3 = AzureChatOpenAI(
    openai_api_type="azure",
    openai_api_base='https://openai-nois-intern.openai.azure.com/',
    openai_api_version="2023-03-15-preview",
    deployment_name='gpt-35-turbo-16k',
    openai_api_key='400568d9a16740b88aff437480544a39',
    temperature=0.5,
    max_tokens=600
)


def run_return_user_response(query, user, token):
    url = f"https://api-hrm.nois.vn/api/chatbot/dayoff?email={user['mail']}"
    headers = {
        "api-key": "2NFGmIbGKlPkedZ25Mo9vQyM0CKSmABieUk-SCGzm9A",
        "token": token,
    }
    response = requests.get(url, headers=headers)

    doc = Document(page_content="text", metadata={"source": "local"})

    print(doc)
    print(response.status_code)
    print(response.json())
    print(user)

    return "thien"
