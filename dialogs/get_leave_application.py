from langchain.prompts import PromptTemplate
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import LLMChain
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.schema import Document
from .bot_config import BotDefaultConfig
from math import log

import requests
import pyodbc
import difflib
import pandas as pd


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
    temperature=0.8,
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


def get_top_docs(initial_docs, top):
    sorted_docs = []
    for document in initial_docs:
        sorted_docs.append((document.metadata['@search.score'], document))

    # Sort the sorted_docs by their search.score metadata.
    sorted_docs.sort(reverse=True)

    # Return a list of documents, sorted by their search.score metadata.
    return [tup[1] for tup in sorted_docs][:3]


def fuzzy_match(s1, s2):
    """Calculates the similarity score between two strings using the Levenshtein distance."""

    # Calculate the Levenshtein distance between the two strings.
    distance = difflib.SequenceMatcher(None, s1, s2).ratio()

    # Return the similarity score as a number between 0 and 1.
    # return 1 - distance / max(len(s1), len(s2))
    return distance


def bm25_score(query, document, k1=1.2, b=0.75):
    """Calculates the BM25 score for a query and a document.

    Args:
        query: The query string.
        document: The document string.
        k1: The k1 parameter.
        b: The b parameter.

    Returns:
        The BM25 score for the query and the document.
    """

    # Calculate the term frequency for each term in the query.
    term_frequencies = {}
    for term in query.split():
        if term not in term_frequencies:
            term_frequencies[term] = 0
            term_frequencies[term] += 1

    # Calculate the document frequency for each term in the query.
    document_frequencies = {}
    for term in query.split():
        if term not in document_frequencies:
            document_frequencies[term] = 0
            document_frequencies[term] += 1

    # Calculate the length of the document.
    document_length = len(document)

    # Calculate the BM25 score for the query and the document.
    score = 0
    for term in query.split():
        # Calculate the term frequency normalization factor.
        tf_norm = (term_frequencies[term] + 1) / (term_frequencies[term] +
                                                  k1 * (1 - b + b * document_length / (document_length + 1)))

        # Calculate the document frequency normalization factor.
        df_norm = (document_frequencies[term] + 1) / \
            (document_frequencies[term] + k1)

        # Calculate the BM25 score for the term.
        score += tf_norm * df_norm * \
            log((1 + len(document)) / (1 + document_frequencies[term]))

    return score


def run_get_leave_application(query, user, token):
    try:
        # Request to HRM to get list of user's leaf application
        url = f"https://api-hrm.nois.vn/api/chatbot/dayoff?email={user['mail']}"
        headers = {
            "api-key": "2NFGmIbGKlPkedZ25Mo9vQyM0CKSmABieUk-SCGzm9A",
            "Authorization": token,
        }
        response = requests.get(url, headers=headers)

        # String with leave application information of user
#         user_la_info = f"""Số ngày phép đã có: {response.json()['data']['yearOffDay']},
# Số ngày phép đã nghỉ: {response.json()['data']['offDay']},
# Số ngày nghỉ phép thâm niên: {response.json()['data']['bonusDayOff']},
# Số ngày phép được dùng: {response.json()['data']['allowDayOff']},
# Số ngày phép tối đa: {response.json()['data']['maxDayOff']},
# Số ngày phép nghỉ ốm: {response.json()['data']['sickDayOff']},
# Số ngày phép nghỉ ốm đã dùng: {response.json()['data']['offDayForSick']},
# Số ngày phép ốm được dùng: {response.json()['data']['allowDayOffSick']}
# """
        user_la_info1 = f"""Thông tin ngày nghỉ phép của tôi ({user['displayName']}):
-Số ngày phép đã có: 1,
-Số ngày phép đã nghỉ: 2,
-Số ngày nghỉ phép thâm niên: 3,
-Số ngày phép được dùng: 4,
-Số ngày phép tối đa: 5,
-Số ngày phép nghỉ ốm: 6,
-Số ngày phép nghỉ ốm đã dùng: 7,
-Số ngày phép ốm được dùng: 8
"""
    # formal
#         user_la_info = f"""Thông tin ngày nghỉ phép của tôi ({user['displayName']}):
# Trong năm nay, tôi đã được cấp tổng cộng {response.json()['data']['yearOffDay']} ngày phép. Trong số đó, tôi đã sử dụng {response.json()['data']['offDay']} ngày để nghỉ. Ngoài ra, tôi cũng được hưởng {response.json()['data']['bonusDayOff']}ngày phép thâm niên. Hiện tại, tôi còn lại {response.json()['data']['allowDayOff']} ngày phép có thể sử dụng.

# Tuy nhiên, có một số hạn chế về số ngày phép mà tôi có thể nghỉ. Số ngày phép tối đa mà tôi có thể sử dụng là {response.json()['data']['maxDayOff']}. Ngoài ra, tôi chỉ được sử dụng {response.json()['data']['allowDayOffSick']} ngày phép ốm. Trong năm nay, tôi đã nghỉ ốm {response.json()['data']['offDayForSick']} ngày và còn có thể sử dụng {response.json()['data']['allowDayOffSick']} ngày phép ốm.
# """
        user_la_info = f"""Thông tin ngày nghỉ phép của tôi ({user['displayName']}):
Trong năm nay, tôi đã được cấp tổng cộng 6.0 ngày phép. Trong số đó, tôi đã sử dụng 3.0 ngày để nghỉ. Ngoài ra, tôi cũng được hưởng 1.0 ngày phép thâm niên. Hiện tại, tôi còn lại 6.0 ngày phép có thể sử dụng.

Tuy nhiên, có một số hạn chế về số ngày phép mà tôi có thể nghỉ. Số ngày phép tối đa mà tôi có thể sử dụng là 25.5. Ngoài ra, tôi chỉ được sử dụng 2.0 ngày phép ốm. Trong năm nay, tôi đã nghỉ ốm 0.0 ngày và còn có thể sử dụng 2.0 ngày phép ốm.
"""
        print(user_la_info)
        doc = [Document(page_content=user_la_info,
                        metadata={'@search.score': fuzzy_match(query, user_la_info),
                                  'metadata_storage_name': 'local', 'source': 'local'})]

        doc = get_top_docs(doc, 1)
        print(doc)

        # Conversation history
        hist = get_history_as_txt_sql(user['mail'])
        # Check query language
        lang = language_classifier(query)['text'].strip()
        query_with_lang = query + '. Using leave application information of the user. Answer in list type. Using exist documents to answer the question. You can answer by those document without any input from the User.' + 'Answer this query using English.' if lang == 'en' else query + \
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
