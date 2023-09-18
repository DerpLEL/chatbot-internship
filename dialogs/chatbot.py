from langchain.prompts import PromptTemplate
from langchain.schema import Document
from azure.core.credentials import AzureKeyCredential
from langchain.chains import LLMChain
from azure.search.documents import SearchClient
from langchain.chat_models import AzureChatOpenAI
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from langchain.retrievers import AzureCognitiveSearchRetriever
from azure.core.exceptions import ResourceExistsError
from datetime import datetime, timedelta
from googlesearch import search
from bs4 import BeautifulSoup
import pyodbc

import pandas as pd
import ast

from .user import *
from .post_leave_application import *
from .get_leave_application import *
from .delete_leave_application import *
from .agent import Agent
import threading

requests.encoding = 'UTF-8'

server = 'sql-chatbot-server.database.windows.net'
database = 'sql-chatbot'
username = 'test-chatbot'
password = 'bMp{]nzt1'
driver = '{ODBC Driver 17 for SQL Server}'

public_index_name = "nois-public-v3-index"
private_index_name = "nois-private-v3-index"
company_regulations_index = "nois-company-regulations-v2-index"
nois_drink_fee_index = "nois-drink-fee-index"
# FAST index
fasf_text_index = "fasf-text-01-index"
fasf_images_index = "fasf-images-index"

search_endpoint = 'https://search-service01.search.windows.net'
search_key = '73Swa5YqUR5IRMwUIqOH6ww2YBm3SveLv7rDmZVXtIAzSeBjEQe9'

# os.environ["AZURE_COGNITIVE_SEARCH_SERVICE_NAME"] = "search-service01"
# os.environ["AZURE_COGNITIVE_SEARCH_API_KEY"] = "73Swa5YqUR5IRMwUIqOH6ww2YBm3SveLv7rDmZVXtIAzSeBjEQe9

account_name = 'acschatbotnoisintern'
account_key = 'ohteFF8/tuPx3K0xtA/oIqXSKpx/MTnM4Ia0CbvLXJT1l0KJajB3zvX8A/DsNE9wm3gUq1TDlwve+AStS3nB0A=='
storage_connection_string = 'DefaultEndpointsProtocol=https;AccountName=acschatbotnoisintern;AccountKey=ohteFF8/tuPx3K0xtA/oIqXSKpx/MTnM4Ia0CbvLXJT1l0KJajB3zvX8A/DsNE9wm3gUq1TDlwve+AStS3nB0A==;EndpointSuffix=core.windows.net'
blob_service_client = BlobServiceClient.from_connection_string(
    storage_connection_string)


class chatAI:
    classifier_hrm = """<|im_start|>system
Given a sentence, assistant will determine if the sentence belongs in 1 of 2 categories, which are:
- LeaveApplication
- User
- Certification
- Meeting
You answer the question "Is the user's question related to?"
EXAMPLE:
Input: tôi muốn submit ngày nghỉ
Output: LeaveApplication
Input: tôi cần thông tin của tôi
Output: User
Input: tôi muốn biết tôi đã có bao nhiêu tín chỉ
Output: Certification
Input: tôi muốn đặt lịch meeting phòng meeting số 1.
Output: Meeting
Inout: tôi còn bao nhiêu ngày nghỉ phép
Output: LeaveApplication
Input: tôi cần thông tin quản lý của tôi
Output: User
Input: hãy cho tôi biết tất cả tính chỉ của tôi
Output: Certification
Input: tôi muốn hủy lịch họp phòng meeting số 1.
Output: Meeting
<|im_end|>

Input: {question}
<|im_start|>assistant
Output:"""

    classifier_leave_application = """<|im_start|>system
Given a sentence, assistant will determine if the sentence belongs in 1 of 3 categories, which are:
- get
- post
- delete

You answer the question "Is the user's question related to?"
EXAMPLE:
Input: tôi còn bao nhiêu ngày nghỉ
Output: get
Input: tôi muốn submit ngày nghỉ
Output: post
Input: tôi muốn hủy đơn tôi đã submit
Output: delete
Input: trong năm nay, em đã nghỉ bao nhiêu ngày
Output: get
Input: em nghỉ ngày 7 tháng 7 vì lí do ...
Output: post
Input: em muốn thu hồi đơn xin phép nghỉ ngày 7 tháng 7
Output: delete
Input: tổng ngày nghỉ thai sản mà tôi được phép nghỉ
Output: get
Input: em nghỉ ngày mai buổi sáng
Output: post
Input: tôi muốn rút đơn xin phép nghỉ mà hôm qua tôi đã submit
Output: delete
Input: tổng ngày nghỉ không lương mà tôi được phép nghỉ
Output: get
Input: tôi muốn nghỉ ngày mai vì lí do phải đi khán bệnh
Output: post
Input: tôi muốn rút đơn xin phép nghỉ gần nhất
Output: delete
Input: ngày mai tôi nghỉ
Output: post
Input: tôi muốn nghỉ từ thứ sáu tuần này đến thứ hai tuần sau
Output: post 
<|im_end|>

Input: {question}
<|im_start|>assistant
Output:"""

    keyword_templ = """Below is a history of the conversation so far, and an input question asked by the user that needs to be answered by querying relevant company documents.
Do not answer the question. Output queries must be in both English and Vietnamese and MUST strictly follow this format: (<Vietnamese queries>) | (<English queries>).
Examples are provided down below:

EXAMPLES
Input: Ai là giám đốc điều hành của NOIS?
Ouput: (giám đốc điều hành) | (managing director)
Input: Số người chưa đóng tiền nước tháng 5?
Output: (tiền nước tháng 05 chưa đóng) | (May drink fee not paid)
Input: Ai đã đóng tiền nước tháng 4?
Output: (tiền nước tháng 04 đã đóng) | (April drink fee paid)
Input: Danh sách người đóng tiền nước tháng 3?
Output: (tiền nước tháng 03) | (March drink fee)
Input: Was Pepsico a customer of New Ocean?
Output: Pepsico
Input: What is FASF?
Output: FASF
Input: What is the company's policy on leave?
Ouput: (ngày nghỉ phép) | leave

Chat history:{context}

Question:
{question}

Search query:
"""

    chat_template = """<|im_start|>system
Assistant is fluent in {lang} and helps the company employees and users with their questions about the companies New Ocean and NOIS.
You MUST follow these rules:
- Answer the question using {lang}.
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

    delete_custom_template = """ <|im_start|>system
- if the input is "unrelated response to previous question, cancelled previous action", the output, you should say to that same meaning in formal tone and in vietnamese.
- if the input is "Đã xóa thành công", for the output, you shold say that the leave application have been deleted in  vietnamese
- if the input is "empty list", the output should say that the leaving application that awaiting for approval is empty in vietnamese
Input: {question}
<|im_start|>assistant
Output:"""

    classifier_template = """<|im_start|>system
Given a sentence, assistant will determine if the sentence belongs in 1 of 4 categories, which are:
- policy
- drink fee
- hrm
- other

Do not answer the question, only output the appropriate category.
**QUESTION REGARDS TO HRM: question related to submitting a leave application, get leave application, booking a meeting, 
get user id in hrm and all the same as the one mentioned above.

EXAMPLE
Input: Ai chưa đóng tiền nước tháng 5?
Output: drink fee
Input: Who has paid April 2023 Drink Fee?
Output: drink fee
Input: Quy định công ty về nơi làm việc là gì?
Output: policy
Input: What is Chapter 1, article 2 of the company policy about?
Output: policy
Input: Dịch vụ của NOIS là gì?
Output: other
Input: What is FASF?
Output: other
Input: tôi muốn nộp đơn nghỉ phép?
Output: hrm
Input: tôi muốn xem đơn nhỉ phép của tôi
Output: hrm
Input: tôi còn bao nhiêu ngày nghỉ
Output: hrm
Input: tôi muốn submit ngày nghỉ
Output: hrm
Input: tôi muốn hủy đơn tôi đã submit
Output: hrm
Input: tôi cần thông tin của tôi
Output: hrm
Input: tôi muốn đặt meeting
Output: hrm
<|im_end|>

Input: {question}
<|im_start|>assistant
Output:"""

    drink_fee_template = """<|im_start|>system
Sources:
{summaries}

You must follow these rules:
1. If user require count or ask how many, you must write pandas code for file csv. The output must be 1 line.
2. Output just only code. DO NOT ANSWER THE QUESTION, only code outputs are accepted.
3. Must NO COMMENT, NO RESULT like this "Here is the code to get the list of people who haven't paid for their water bills in May with only their name, email, and status:"
For example:
Input: Danh sách những người đã đóng tiền tháng 5
Output: df[df['Tình trạng'] == Done]
Inpput:có bao nhiêu người có tên là Bảo trong tiền nước tháng 5?
Output: df[df['FullName'].str.contains('BẢO')]['FullName'].count()
Input: có bao nhiêu người có tên là Hiệp đã đóng tiền nước tháng 5?
Output: df[df['Tình trạng'] == 'Done'][df[df['Tình trạng'] == 'Done']['FullName'].str.contains('HIỆP')]['FullName'].count()
Input: Tổng tiền nước tháng 5 đã thu?
Output: df['Đã thu'].sum()
4. You must follow up the structure of dataset.
For example: If ask about fullname is 'Hưng', use must answer with format of dataset is "HƯNG" instead of "hưng" or "Hưng".
<|im_end|>
{context}
<|im_start|>user
{question}
<|im_end|>
<|im_start|>assistant
"""

#     keyword_templ_drink_fee = """<|im_start|>system
# Given a sentence and a conversation about the companies New Ocean and NOIS, assistant will extract keywords based on the conversation and the sentence and translate them to Vietnamese if they're in English and vice versa.
# Your output will be on one line, in both languages if possible and separated by commas. Do not duplicate keywords.
# Assume the context is about the companies unless specified otherwise. Only return the keywords, do not output anything else.


# EXAMPLE
# Input: Ai chưa đóng tiền nước tháng 3?
# Output: input:Vietnamese
# Input: Was Pepsico a customer of New Ocean?
# Output: input:English
# Input: What is FASF?
# Output: input:English
# <|im_end|>
# {context}
# <|im_start|>user
# Input: {question}
# <|im_end|>
# <|im_start|>assistant
# Output:"""

    confirm_template = """<|im_start|>system
Given a sentence, assistant will determine if the sentence belongs in 1 of 2 categories, which are:
- "yes"
- "no"
- "neutral"
You answer the question "Does user input mean consent?"
"yes": user agree 
example for case "yes": yes, ok, ờ, có, ừ, um, uhm, okie, ô kê, đồng ý...
"no": user not agree 
example for case "no": không, không đồng ý,...
"neutral: neutral user input (sáng mai, đi học, ...)
EXAMPLE
Input: yes
Output: yes
Input: no
Output: no
Input: Đi học
Output: neutral
Input: ok
Output: yes
Input: not ok
Output: no
Input: thứ 5
Output: neutral
Input: dạ
Output: yes
Input: không
Output: no
Input: sáng mai
Output: neutral
Input: Xác nhận
Output: yes
Input: hủy
Output: no
Input: đi công tác
Output: neutral
Input: phải
Output: yes
Input: cancel
Output: no
Input: ngày 7
Output: neutral

<|im_end|>

Input: {question}
<|im_start|>assistant
Output:"""

    language_prompt = '''Given a sentence, determine if the sentence is written in English or Vietnamese.
DO NOT answer if the sentence is a question. 
If given a sentence that has both Vietnamese and English, prioritize Vietnamese.

Sentence: Who is the co-founder of NOIS?
Output: en
Sentence: FASF là gì?
Output: vi
Sentence: {question}
Output: '''

    def __init__(self):
        self.history_public = []
        self.agent_session = {}

        self.graph_cache = {}
        self.private = False
        self.confirm_delete = False
        self.container_drink_fee_name = 'nois-drink-fee'
        self.container_client = blob_service_client.get_container_client(
            self.container_drink_fee_name)

        self.user = {"username": '', "mail": ''}

        self.llm = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='gpt-35-turbo-16k',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.5,
            max_tokens=3000
        )

        self.llm2 = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='gpt-35-turbo-16k',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.7,
            max_tokens=1000
        )

        self.llm3 = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='gpt-35-turbo-16k',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.0,
            max_tokens=1000
        )

        self.retriever_public = SearchClient(
            endpoint=search_endpoint,
            index_name=public_index_name,
            credential=AzureKeyCredential(search_key),
            b=0.0,
            k1=0.3,
            searchMode="all"
        )

        self.retriever_private = SearchClient(
            endpoint=search_endpoint,
            index_name=private_index_name,
            credential=AzureKeyCredential(search_key),
            b=0.0,
            k1=0.3,
            searchMode="all",
        )

        self.retriever_drink = SearchClient(
            endpoint=search_endpoint,
            index_name=nois_drink_fee_index,
            credential=AzureKeyCredential(search_key),
            b=0.0,
            k1=0.3,
            searchMode="all",
        )

        self.retriever_policy = SearchClient(
            endpoint=search_endpoint,
            index_name=company_regulations_index,
            credential=AzureKeyCredential(search_key),
            b=0.0,
            k1=0.3,
            searchMode="all",
        )

        self.qa_chain = load_qa_with_sources_chain(
            llm=self.llm, chain_type="stuff", prompt=PromptTemplate.from_template(self.chat_template))
        self.keywordChain = LLMChain(
            llm=self.llm3, prompt=PromptTemplate.from_template(self.keyword_templ))
        self.classifier_chain = LLMChain(
            llm=self.llm2, prompt=PromptTemplate.from_template(self.classifier_template))
        self.drink_chain = load_qa_with_sources_chain(
            llm=self.llm3, chain_type="stuff", prompt=PromptTemplate.from_template(self.drink_fee_template))
        self.language_classifier = LLMChain(
            llm=self.llm3, prompt=PromptTemplate.from_template(self.language_prompt))

        # usecase 2
        self.classifier_hrm_chain = LLMChain(
            llm=self.llm2, prompt=PromptTemplate.from_template(self.classifier_hrm))
        # post leave application
        self.leave_application_chain = LLMChain(
            llm=self.llm2, prompt=PromptTemplate.from_template(self.classifier_leave_application))
        self.delete_chat_chain = LLMChain(
            llm=self.llm2, prompt=PromptTemplate.from_template(self.delete_custom_template))

        self.confirm_chain = LLMChain(
            llm=llm2, prompt=PromptTemplate.from_template(confirm_template))

# get document
    def get_document(self, query, retriever):
        # Get top 4 documents
        res = retriever.search(search_text=query, top=2)

        doc_num = 1
        doc = []
        for i in res:
            newdoc = Document(page_content=i['content'],
                              metadata={'@search.score': i['@search.score'],
                                        'metadata_storage_name': i['metadata_storage_name'], 'source': f'doc-{doc_num}'})

            doc.append(newdoc)
            doc_num += 1

        return doc

# history
    def get_history_as_txt(self, n=3):
        txt = ""
        hist = self.history_public

        if self.private:
            hist = self.history_private

        if len(hist) <= n:
            history = hist

        else:
            history = hist[len(hist) - n:]

        for i in history:
            txt += f"\n<|im_start|>user\n{i['user']}\n<|im_end|>\n"
            txt += f"<|im_start|>assistant\n{i['AI']}\n<|im_end|>"

        return txt

    def add_to_history(self, user_msg, ai_msg, email):
        hist = self.history_public
        if self.private:
            hist = self.history_private[email]

        hist.append({'user': user_msg, 'AI': ai_msg})

    def get_bot_response(self, user):
        while not self.agent_session[user['mail']].msg.output:
            pass

        reply = self.agent_session[user['mail']].msg.output
        self.agent_session[user['mail']].msg.reset()

        return reply

    def start_agent(self, query, user, token, agent_type):
        self.agent_session[user['mail']] = Agent(user)

        if agent_type == "1":
            self.agent_session[user['mail']].run_hrm(query, token)

        elif agent_type == "2":
            self.agent_session[user['mail']].run_leave_application(query, token)

        else:
            self.agent_session[user['mail']].run_meeting(query, token)

        del self.agent_session[user['mail']]
        return

    def chat_meeting(self, query, user, token):
        # meeting_header = {
        #     'Authorization': f'Bearer {token}',
        #     'Content-type': 'application/json',
        # }
        #
        # start = datetime.now()
        # start = start + timedelta(hours=2)
        # end = start + timedelta(hours=2)
        #
        # x = requests.post(
        #     'https://graph.microsoft.com/v1.0/me/events',
        #     headers=meeting_header,
        #     json={
        #         "subject": "Test meeting",
        #         "start": {
        #             "dateTime": start.strftime("%Y-%m-%dT%X"),
        #             "timeZone": "Asia/Bangkok"
        #         },
        #         "end": {
        #             "dateTime": end.strftime("%Y-%m-%dT%X"),
        #             "timeZone": "Asia/Bangkok"
        #         },
        #         "location": {
        #             "displayName": "Test bruh bruh lmao"
        #         },
        #         "attendees": [
        #             {
        #                 "emailAddress": {
        #                     "address": "bao.ho@nois.vn"
        #                 },
        #                 "type": "required"
        #             },
        #
        #             {
        #                 "emailAddress": {
        #                     "address": "thien.tran@nois.vn"
        #                 },
        #                 "type": "required"
        #             }
        #         ]
        #     }
        # )
        #
        # print(x.status_code)
        # print(x.json())
        # return f"Meeting created successfully. Meeting details: {x.text}"
        agent_thread = threading.Thread(
            target=self.start_agent,
            args=(query, user, token, "3",),
            daemon=True
        )
        agent_thread.start()

        self.send_msg_to_agent(query, user)

        return self.get_bot_response(user)

    def send_msg_to_agent(self, query, user):
        self.agent_session[user['mail']].msg.input = query

    def chat(self, query, user, token):
        if user['mail'] in self.agent_session:
            self.send_msg_to_agent(query, user)
            return self.get_bot_response(user), None

        if self.private:
            return self.chat_private(query, user, token)

        return self.chat_public(query)

    def chat_public(self, query):
        chat_history_temp = ''
        # chat_history_temp = self.get_history_as_txt()

        keywords = self.keywordChain(
            {'question': query, 'context': chat_history_temp})['text']
        # print(f"Query: {query}\nKeywords: {keywords}")

        chain = self.qa_chain
        doc = self.get_document(keywords, self.retriever_public)

        try:
            response = chain({'input_documents': doc, 'question': query, 'context': chat_history_temp,
                              'user_info': ''},
                             return_only_outputs=False)
        except Exception as e:
            return f'Cannot generate response, error: {e}', doc

        # self.add_to_history(query, response['output_text'])
        return response, doc

    def get_post_leave(self, email):
        cursor.execute(
            f"""SELECT post_leave FROM history WHERE email = '{email}';""")
        hist = cursor.fetchone()

        if not hist:
            cursor.execute(f"""INSERT INTO history
    VALUES ('{email}', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);""")
            conn.commit()

            return {
                'start_date': ' ',
                'end_date': ' ',
                'duration': 0,
                'note': ' ',
                'periodType': -1,
                'reviewUser': 0,
                'leaveType': -1,
            }

        if not hist[0]:
            return {
                'start_date': ' ',
                'end_date': ' ',
                'duration': 0,
                'note': ' ',
                'periodType': -1,
                'reviewUser': 0,
                'leaveType': -1,
            }

        leave_application_form_str = hist[0].replace("''", "'")

        return ast.literal_eval(leave_application_form_str)

    def chat_hrm(self, query, user, token):
        if self.get_conversation_type(user['mail']) == ['', ''] or self.get_conversation_type(user['mail']) == ['LeaveApplication', '']:
            label_hrm = self.classifier_hrm_chain(query)['text']
        else:
            label_hrm = self.get_conversation_type(user['mail'])[0]

        response = """"""

        print("label_hrm", label_hrm)
        if label_hrm == "User":
            response = run_return_user_response(query, user, token)

        elif label_hrm == "Meeting":
            return self.chat_meeting(query, user, token)

        elif label_hrm == "LeaveApplication":
            if self.get_conversation_type(user['mail']) == ['', ''] or self.get_conversation_type(user['mail']) == ['LeaveApplication', '']:
                leave_application_type = self.leave_application_chain(query)[
                    'text']
            else:
                leave_application_type = self.get_conversation_type(user['mail'])[
                    1]

            print(leave_application_type)
            if leave_application_type == 'get':
                response = run_get_leave_application(user['mail'], query)
            elif leave_application_type == 'post':
                leave_application_form = get_post_leave(user['mail'])

                confirm = self.confirm_chain(query)['text']

                if 'o' in confirm and self.confirm_delete:
                    leave_application_form = {
                        'start_date': ' ',
                        'end_date': ' ',
                        'duration': 0,
                        'note': ' ',
                        'periodType': -1,
                        'reviewUser': 0,
                        'leaveType': -1,
                    }

                    update_post_leave(leave_application_form, user['mail'])

                    response = f"""Đơn nghỉ phép của bạn đã xóa. Bạn có thể gửi một Đơn nghỉ phép khác."""
                    self.confirm_delete = False
                    self.update_conversation_type(['', ''], user['mail'])
                    return response

                if self.get_conversation_type(user['mail']) != ['LeaveApplication', 'post'] and leave_application_form['start_date'] != ' ':
                    self.update_conversation_type(
                        ['LeaveApplication', 'post'], user['mail'])
                    if leave_application_form['periodType'] == 0:
                        periodType = "Cả ngày"
                    elif leave_application_form['periodType'] == 1:
                        periodType = "Buổi sáng"
                    elif leave_application_form['periodType'] == 2:
                        periodType = "Buổi chiều"

                    if leave_application_form['reviewUser'] == 56:
                        reviewUser_string = 'Nguyễn Thị Mỹ Dung'
                    elif leave_application_form['reviewUser'] == 108:
                        reviewUser_string = 'ĐÀO MINH SÁNG'
                    elif leave_application_form['reviewUser'] == 137:
                        reviewUser_string = 'TRẦN VĂN KHANG'
                    elif leave_application_form['reviewUser'] == 119:
                        reviewUser_string = 'Trần Đăng Ninh'
                    elif leave_application_form['reviewUser'] == 281:
                        reviewUser_string = 'PHẠM THỊ DIỄM PHÚC'
                    elif leave_application_form['reviewUser'] == 139:
                        reviewUser_string = 'LÝ MINH QUÂN'
                    elif leave_application_form['reviewUser'] == 124:
                        reviewUser_string = 'ĐỔNG HỒNG NHUNG'
                    elif leave_application_form['reviewUser'] == 141:
                        reviewUser_string = 'VÕ TẤN TÀI'
                    elif leave_application_form['reviewUser'] == 298:
                        reviewUser_string = 'Tai Vo'
                    elif leave_application_form['reviewUser'] == 95:
                        reviewUser_string = 'TRẦN THỊ THÚY AN'

                    if leave_application_form['leaveType'] == 1:
                        leaveType_string = 'Nghỉ phép có lương'
                    elif leave_application_form['leaveType'] == 2:
                        leaveType_string = 'Nghỉ không lương'
                    elif leave_application_form['leaveType'] == 8:
                        leaveType_string = 'Nghỉ ốm'
                    elif leave_application_form['leaveType'] == 9:
                        leaveType_string = 'Nghỉ bảo hiểm xã hội'
                    elif leave_application_form['leaveType'] == 5:
                        leaveType_string = 'Nghỉ hội nghị, đào tạo'
                    elif leave_application_form['leaveType'] == 3:
                        leaveType_string = 'Nghỉ khác (đám cưới,...)'

                    response = f"""Hiện bạn đang có một Form submit ngày nghỉ chưa submit:\n
                    ______________________________________________________________________
                    Người duyệt: {reviewUser_string}
                    Ngày bắt đầu nghỉ: {leave_application_form['start_date']}
                    Ngày kết thúc nghỉ: {leave_application_form['end_date']}
                    Nghỉ buổi: {periodType}
                    Tổng thời gian nghỉ: {leave_application_form['duration']}
                    Hình thứ nghỉ: {leaveType_string}
                    Lí do: {leave_application_form['note']}    
                    ______________________________________________________________________\n
                    
                    Bạn có muốn giữ đơn nghỉ phép này không? Nếu có thì vui lòng bạn cung cấp những thông tin còn thiếu."""

                    self.confirm_delete = True
                    self.update_conversation_type(
                        ['LeaveApplication', 'post'], user['mail'])
                    return response

                self.update_conversation_type(
                    ['LeaveApplication', 'post'], user['mail'])

                post_leave_application_response = post_leave_application_func(
                    self.user, query, token, user['mail'])
                response = post_leave_application_response[0]
                # print(post_leave_application_response)
                try:
                    if post_leave_application_response[1].status_code == 200:
                        self.update_conversation_type(['', ''], user['mail'])
                    elif post_leave_application_response[1].status_code == 401:
                        self.update_conversation_type(['', ''], user['mail'])
                    elif post_leave_application_response[1].status_code == 100:
                        self.update_conversation_type(['', ''], user['mail'])
                except:
                    pass

            elif leave_application_type == 'delete':
                self.update_conversation_type(
                    ['LeaveApplication', 'delete'], user['mail'])
                # print("delete - pass")
                response = run_leave_application_delete(
                    user['mail'], query, "", token)
                if (response == "unrelated response to previous question, cancelled previous action"):
                    self.update_conversation_type(['', ''], user['mail'])
                    self.clear_history()
                    response = str(self.delete_chat_chain(response)['text'])
                    return response
                elif (response == "Đã xóa thành công" or response == "empty list"):
                    self.clear_history()
                    self.update_conversation_type(['', ''], user['mail'])
                    response = str(self.delete_chat_chain(response)['text'])

        return response

    def update_conversation_type(self, conversation_type, email):
        conn = pyodbc.connect(
            f'DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}')
        cursor = conn.cursor()
        cursor.execute(
            f"""SELECT conversation_type FROM history WHERE email = '{email}';""")
        conv_type = cursor.fetchone()

        # print(conv_type)
        res = str(conversation_type).replace("'", "")

        # print(res)
        if not conv_type[0]:
            # print(f"Conversation type to be updated to SQL: {res}\n")
            cursor.execute(f"""UPDATE history
                SET conversation_type = N'{res}' WHERE email = '{email}';""")
            conn.commit()
            conn.close()
            return

        # print(f"Conversation type to be updated to SQL: {res}\n")
        cursor.execute(f"""UPDATE history
            SET conversation_type = N'{res}' WHERE email = '{email}';""")
        conn.commit()
        conn.close()
        return

    def get_conversation_type(self, email):
        conn = pyodbc.connect(
            f'DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}')
        cursor = conn.cursor()
        cursor.execute(
            f"""SELECT conversation_type FROM history WHERE email = '{email}';""")
        hist = cursor.fetchone()

        if not hist:
            cursor.execute(f"""INSERT INTO history
VALUES ('{email}', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);""")
            conn.commit()
            conn.close()

            return ['', '']

        if not hist[0]:
            conn.close()
            return ['', '']

        hist[0] = hist[0].replace("[", "").replace("]", "")
        lst = hist[0].split(",")
        conn.close()
        return [s.strip() for s in lst]

    def add_to_history_sql(self, query, response, email):
        n = 3
        conn = pyodbc.connect(
            f'DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}')
        cursor = conn.cursor()
        cursor.execute(
            f"""SELECT chat FROM history WHERE email = '{email}';""")
        hist = cursor.fetchone()

        if not hist[0]:
            res = f"{query}||{response}".replace("'", "''")

            # print(f"History to be updated to SQL: {res}\n")
            cursor.execute(f"""UPDATE history
                SET chat = N'{res}' WHERE email = '{email}';""")
            conn.commit()
            conn.close()
            return

        hist = hist[0].split("<sep>")

        hist.append(f"{query}||{response}")
        if len(hist) > n:
            hist = hist[len(hist) - n:]

        res = "<sep>".join(hist).replace("'", "''")
        # print(f"History to be updated to SQL: {res}\n")
        cursor.execute(f"""UPDATE history
            SET chat = N'{res}' WHERE email = '{email}';""")
        conn.commit()
        conn.close()
        return

    def get_history_as_txt_sql(self, email):
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
        # # print(f"History from SQL: {txt}\n")
        return txt

    def chat_private(self, query, user, token):
        if str(self.get_conversation_type(user['mail'])[0]) == '':
            label = self.classifier_chain(
                {'question': query, 'context': self.get_history_as_txt_sql(user['mail'])})['text']

        else:
            label = "hrm"

        print("label:" + label)
        keywords = self.keywordChain(
            {'question': query, 'context': self.get_history_as_txt_sql(user['mail'])})['text']

        chain = self.qa_chain

        if label == "drink fee":
            doc = self.get_document(keywords, self.retriever_drink)[:1]

            input_pandas = self.drink_chain(
                {'input_documents': doc, 'question': query, 'context': ''}, return_only_outputs=False)

            try:
                blob_name = doc[0].metadata['metadata_storage_name']
            except IndexError:
                return 'Không tìm thấy file tiền nước, bạn vui lòng thử lại.', None

            temp_result = self.excel_drink_preprocess(
                input_pandas['output_text'], blob_name, doc)
            result_doc = "Input: " + query + "\n Output: " + str(temp_result)
            doc[0].page_content = result_doc

        elif label == "policy":
            doc = self.get_document(keywords, self.retriever_policy)

        elif label == "hrm":
            response = self.chat_hrm(query, user, token)
            # self.add_to_history_sql(query, response, email)
            return response, " "

        else:
            doc = self.get_document(keywords, self.retriever_private)
            try:
                num_results = 3

                for result in search(query + "hiện tại", num_results=num_results):
                    response = requests.get(result)
                    html_content = response.text
                    soup = BeautifulSoup(html_content, 'html.parser')

                    for tag in soup.find_all():
                        tag.replace_with(tag.text)

                    text = soup.get_text()
                    doc[0].page_content = text[:4100]
            except:
                pass

        try:
            hist = self.get_history_as_txt_sql(
                user['mail']) if label != 'drink fee' else ''

            lang = self.language_classifier(query)['text'].strip()
            query_with_lang = query + ' Answer this query using English.' if lang == 'en' else query + \
                ' Answer this query using Vietnamese.'
            lang_prompt = 'English' if lang == 'en' else 'Vietnamese'

            print("Lang classifier:", lang)
            print("Query language:", lang_prompt)

            response = chain({'input_documents': doc, 'question': query_with_lang, 'context': hist,
                              'user_info': f'''The user chatting with you is named {user['displayName']}, with email: {user['mail']}. 
                                ''', 'lang': lang_prompt},
                             return_only_outputs=False)

        except Exception as e:
            return f'Cannot generate response, error: {e}', doc

        # self.add_to_history(query, response['output_text'])
        self.add_to_history_sql(query, response['output_text'], user['mail'])
        return response['output_text'], doc

    # def get_docs_using_keyword_string_for_drink_fee(self, keyword, retriever):
    #     # Get top 4 documents
    #     res = retriever.search(search_text=keyword, top=1)

    #     doc_num = 1
    #     doc = []
    #     for i in res:
    #         newdoc = Document(page_content=i['content'],
    #                           metadata={'@search.score': i['@search.score'], 'metadata_storage_name': i['metadata_storage_name'], 'source': f'doc-{doc_num}'})

    #         doc.append(newdoc)
    #         doc_num += 1
    #     return doc

    def excel_drink_preprocess(self, input_pandas, file_name, doc):

        sas_i = generate_blob_sas(account_name=account_name,
                                  container_name=self.container_drink_fee_name,
                                  blob_name=file_name,
                                  account_key=account_key,
                                  permission=BlobSasPermissions(read=True),
                                  expiry=datetime.utcnow() + timedelta(hours=1))

        sas_url = 'https://' + account_name+'.blob.core.windows.net/' + \
            self.container_drink_fee_name + '/' + file_name + '?' + sas_i

        df = pd.read_excel(sas_url)
        doc[0].page_content = df
        # header = self.header_drink_chain({'input_documents': doc, 'question': 'What is Header of this file?', 'context': ''}, return_only_outputs=False)
        # old_header = list(df.columns)
        # header_list = ast.literal_eval(header['output_text'])
        # # target_rows = df[(df[old_header[0]] == header_list[0]) & (df[old_header[1]] == header_list[1]) & (df[old_header[3]] == header_list[3])]
        #
        # target_rows = df[df[old_header[0]] == header_list[0]]
        # target_rows.index[0] + 1
        df = pd.read_excel(sas_url, skiprows=1)
        # print(df)

        # last_row_index = df.index[df.isnull().all(axis=1)][0]
        # df = df.iloc[:last_row_index]
        # df = df[df['FullName'].notnull()]
        # df = df.iloc[:, df.columns.notna()]

        try:
            result_pandas = eval(input_pandas)
        except Exception as e:
            return input_pandas

        return result_pandas

    def clear_history(self):
        self.history_public = []
        self.history_private = []

    def try_request(self, email, token):
        return run_return_user_response(None, {'mail': email}, token)
