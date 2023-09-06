from langchain.prompts import PromptTemplate
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import LLMChain
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.schema import Document
from .bot_config import BotDefaultConfig

import requests
import pyodbc

requests.encoding = 'UTF-8'

BOT_CONFIG = BotDefaultConfig()

server = BOT_CONFIG.SERVER
database = BOT_CONFIG.DATABASE
username = BOT_CONFIG.USERNAME
password = BOT_CONFIG.PASSWORD
driver = BOT_CONFIG.DRIVER


# Prompt template for LLM
chat_template = """<|im_start|>system
Assistant helps the company employees and users with their questions about the companies New Ocean and NOIS. Your answer must adhere to the following criteria:
You MUST follow this rule:
- If question is in English, answer in English. If question is in Vietnamese, answer in Vietnamese. 
- Be friendly in your answers. You may use the provided sources to help answer the question. If there isn't enough information, say you don't know. If asking a clarifying question to the user would help, ask the question.
- If the user greets you, respond accordingly.

{user_info}

Sources:
{summaries}
<|im_end|>

Chat history:{context}

<|im_start|>user
{question}
<|im_end|>
<|im_start|>assistant
"""

language_prompt = '''Given a sentence, determine if the sentence is written in English or Vietnamese.
Output en for English, and vi for Vietnamese. DO NOT answer if the sentence is a question.
If given a sentence that has both Vietnamese and English, prioritize Vietnamese.

Sentence: Who is the co-founder of NOIS?
Output: en
Sentence: FASF là gì?
Output: vi
Sentence: {question}
Output: '''

# Large Language Model
llm = AzureChatOpenAI(
    openai_api_type="azure",
    openai_api_base='https://openai-nois-intern.openai.azure.com/',
    openai_api_version="2023-03-15-preview",
    deployment_name='gpt-35-turbo-16k',
    openai_api_key='400568d9a16740b88aff437480544a39',
    temperature=0.5,
    max_tokens=3000
)

llm2 = AzureChatOpenAI(
    openai_api_type="azure",
    openai_api_base='https://openai-nois-intern.openai.azure.com/',
    openai_api_version="2023-03-15-preview",
    deployment_name='gpt-35-turbo-16k',
    openai_api_key='400568d9a16740b88aff437480544a39',
    temperature=0.7,
    max_tokens=600
)

llm3 = AzureChatOpenAI(
    openai_api_type="azure",
    openai_api_base='https://openai-nois-intern.openai.azure.com/',
    openai_api_version="2023-03-15-preview",
    deployment_name='gpt-35-turbo-16k',
    openai_api_key='400568d9a16740b88aff437480544a39',
    temperature=0.5,
    max_tokens=600
)

# chain for creating answer from bot
qa_chain = load_qa_with_sources_chain(
    llm=llm, chain_type="stuff", prompt=PromptTemplate.from_template(chat_template))
language_classifier = LLMChain(
    llm=llm3, prompt=PromptTemplate.from_template(language_prompt))


"""
get history conversation of user
- input: mail of user
- output: history conversation of user
"""


def get_history_as_txt_sql(email):
    conn = pyodbc.connect(
        f'DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}')
    cursor = conn.cursor()
    cursor.execute(
        f"""SELECT chat FROM history WHERE email = '{email}';""")
    hist = cursor.fetchone()

    if not hist:
        cursor.execute(f"""INSERT INTO history
VALUES ('{email}', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);""")
        conn.commit()
        conn.close()
        return ""

    if not hist[0]:
        conn.close()
        return ""

    hist = hist[0].split("<sep>")

    txt = ""
    for row in hist:
        i = row.split('||')

        try:
            txt += f"\n<|im_start|>user\n{i[0]}\n<|im_end|>\n"
            txt += f"<|im_start|>assistant\n{i[1]}\n<|im_end|>"
        except IndexError:
            break

    conn.close()
    return txt


"""
function for return information of user: name, phone, mail, manager,...
- input: query of user, information of user, token of Graph Authentication of User
- output: response to query of user
"""


def run_return_user_response(query, user, token):
    try:
        # Request to HRM to get list of user's mangers
        url = f"https://api-hrm.nois.vn/api/chatbot/my-managers?email={user['mail']}"
        headers = {
            "api-key": "2NFGmIbGKlPkedZ25Mo9vQyM0CKSmABieUk-SCGzm9A",
            "token": token,
        }
        response = requests.get(url, headers=headers)

        list_manager = ''
        count_manager = 1
        for item in response.json()['data']:
            list_manager += str(count_manager) + '. ' + str(item['fullName']) + \
                ', userId:' + str(item['userId']) + '\n'
            count_manager += 1

        # String with information of user
        user_info = f"""user: My name is {user['displayName']},
My job is {user['jobTitle']}, 
My mail is {user['mail']},
My department is {user['department']},
My mobilePhone is {user['mobilePhone']},
My officeLocation is {user['officeLocation']},
My department is {user['department']},
My Company Name is New Ocean Information System Company Limited.
My list of mangers:
{list_manager}
"""
        # Document for chain
        doc = [Document(page_content=user_info,
                        metadata={'@search.score': 100,
                                  'metadata_storage_name': 'local', 'source': 'local'})]
        # Conversation history
        hist = get_history_as_txt_sql(user['mail'])
        # Check query language
        lang = language_classifier(query)['text'].strip()
        query_with_lang = query + ' Answer this query using English.' if lang == 'en' else query + \
            ' Answer this query using Vietnamese.'
        lang_prompt = 'English' if lang == 'en' else 'Vietnamese'

        # Create response
        response = qa_chain({'input_documents': doc, 'question': query_with_lang, 'context': hist,
                            'user_info': f'''The user chatting with you is named {user['displayName']}, with email: {user['mail']}. 
                            ''', 'lang': lang_prompt},
                            return_only_outputs=False)
        
        return response['output_text']
    
    except Exception as e:
        print(e)
        pass
