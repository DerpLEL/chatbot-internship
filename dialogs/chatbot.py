from langchain.prompts   import PromptTemplate
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

requests.encoding = 'UTF-8'

server = 'sql-chatbot-server.database.windows.net'
database = 'sql-chatbot'
username = 'test-chatbot'
password = 'bMp{]nzt1'
driver= '{ODBC Driver 17 for SQL Server}'

conn = pyodbc.connect(f'DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}')
cursor = conn.cursor()


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
blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6Ii1LSTNROW5OUjdiUm9meG1lWm9YcWJIWkdldyJ9.eyJhdWQiOiI1OWI2N2I2YS1lNWYwLTQ1MzYtOTVmMy1hMzY3ZmY2OWVkODUiLCJpc3MiOiJodHRwczovL2xvZ2luLm1pY3Jvc29mdG9ubGluZS5jb20vNWUyYTNjYmQtMWE1Mi00NWFkLWI1MTQtYWI0Mjk1NmIzNzJjL3YyLjAiLCJpYXQiOjE2OTA4NjMxNjgsIm5iZiI6MTY5MDg2MzE2OCwiZXhwIjoxNjkwODY4NDA5LCJhaW8iOiJBV1FBbS84VUFBQUExRTEvSmZCV2RneFhGNTViNURTUGRjTU85THN6Sk54QnU4aGpGR1I5RnFiaGxPcmhIa1UyeFJCYUliM1gwcDlCYU8xSWtiSmVUcHZTNlVXTE8rZHdaekx1QUhQQ1ZGY25kaUxaMVY2S1JBNXhGck9OaS9NdWVrOWIyclpPRG45SCIsImF6cCI6Ijc2ZWE5MmQ2LTMzMDgtNDBkNS04NjRhLWIyN2ZiOGY1YjI3MyIsImF6cGFjciI6IjAiLCJuYW1lIjoiVGhpZW4gVHJhbiIsIm9pZCI6ImY1MjdhZGI1LWM5OGMtNDg4NS1iYjY3LThkMTc4NTI2ZDI1NCIsInByZWZlcnJlZF91c2VybmFtZSI6InRoaWVuLnRyYW5Abm9pcy52biIsInJoIjoiMC5BVWtBdlR3cVhsSWFyVVcxRkt0Q2xXczNMR3A3dGxudzVUWkZsZk9qWl85cDdZVkpBSE0uIiwicm9sZXMiOlsiVXNlciJdLCJzY3AiOiJhY2Nlc3NfYXNfdXNlciIsInN1YiI6Ik1oTGgzVnBVU2V1VE1FN2xlcjZ6Vk9VSno0Qkx6c3J0S2I4NTh3R1owMUkiLCJ0aWQiOiI1ZTJhM2NiZC0xYTUyLTQ1YWQtYjUxNC1hYjQyOTU2YjM3MmMiLCJ1dGkiOiIwVzJfVk1QMHYwMm5jWkVabFMwcEFBIiwidmVyIjoiMi4wIn0.U2_xKL1VK3A9NK08qT70TsYlL3dMoKSSy3gCyz4C_D1hoHT-dPKxC0oBhDMxSwtvenwcJig3oSsvuwVsIUQBJjDIdjcVp-QU30AogWG4RHL5fuAYE-yToKViALInhMz28zH75zztUN2iYlXEy4MA0gEHtgQ1xRoI_TuiuS04VI_potBsBpNPZJEf-_W1p_klYKGGXAjxxbzuhj8azvffRFdYYyWITRZrAYqH1nHOoIbWNNq3f1YdHZAXILdjL2n5tMTyIRlXUweB0BM8atKkkMh86qiInVD2VFtWXuvoAXkFwq6XrX0wVB_0FQzPz_J52spC5jLFhixp5099Q8osXQ"

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
Assistant helps the company employees and users with their questions about the companies New Ocean and NOIS. Your answer must adhere to the following criteria:
You MUST follow this rule:
- If question is in English, answer in English. If question is in Vietnamese, answer in Vietnamese. 
- Be brief but friendly in your answers. You may use the provided sources to help answer the question. If there isn't enough information, say you don't know. If asking a clarifying question to the user would help, ask the question.
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

    classifier_template = """<|im_start|>system
Given a sentence, assistant will determine if the sentence belongs in 1 of 3 categories, which are:
- policy
- drink fee
- hrm
- other

Do not answer the question,     `only output the appropriate category.
**QUESTION REGARDS TO HRM: question related to submitting a leave application, get leave application, 
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
<|im_end|>

Input: {question}
<|im_start|>assistant
Output:"""

    drink_fee_template = """<|im_start|>system
Sources:
{summaries}

You must follow this rule:
1. If user require count or ask how many, you must write pandas code for file csv. The output must be 1 line.
2. Output just only code.
3. Must NO COMMENT, NO RESULT like this "Here is the code to get the list of people who haven't paid for their water bills in May with only their name, email, and status:"
For example:
Input: Danh sách những người đã đóng tiền tháng 5
Output: df[df['Tình trạng'] == Done]
Inpput:có bao nhiêu người có tên là Bảo trong tiền nước tháng 5?
Output: df[df['FullName'].str.contains('BẢO')]['FullName'].count()
Input: có bao nhiêu người có tên là Hiệp đã đóng tiền nước tháng 5?
Output: df[df['Tình trạng'] == 'Done'][df[df['Tình trạng'] == 'Done']['FullName'].str.contains('HIỆP')]['FullName'].count()
4. You must follow up the structure of dataset.
For example: If ask aboout fullname is 'Hưng', use must answer with format of dataset is "HƯNG" instead of "hưng" or "Hưng".
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

    header_templ_drink_fee = """<|im_start|>system
Sources:
{summaries}

You must follow this rule:
1. You will answer the question "What are header of this file?".
2. Your answer is in list type which includes all header of that file.
3. Output just only code.
4. Must NO COMMENT, NO RESULT.

For Example:
- Input:
BẢNG TỔNG HỢP TIỀN NƯỚC THÁNG 04/2023 Unnamed: 1 Unnamed: 2 Unnamed: 3 Unnamed: 4 Unnamed: 5 Unnamed: 6 Unnamed: 7 Unnamed: 8
0 STT Email FullName April Total Thực thu Note Tình trạng NaN NaN
1 1 hung.bui@nois.vn BÙI TUẤN HƯNG 78200 78200 NaN Done NaN NaN
2 2 hiep.dang@nois.vn ĐẶNG DUY HIỆP 30700 30700 NaN Done NaN NaN
3 3 tai.dang@nois.vn ĐẶNG HỮU TÀI 22500 22500 NaN Done NaN NaN
4 4 sang.dao@nois.vn ĐÀO MINH SÁNG 5000 NaN NaN NaN NaN NaN
5 5 nam.do@nois.vn ĐỖ NGỌC NAM 6500 6500 NaN Done NaN NaN
- Output:
['STT', 'Email', 'FullName', 'April Total', 'Thực thu', 'Note', 'Tình trạng', 'NaN', 'NaN']

<|im_end|>
{context}
<|im_start|>user
{question}
<|im_end|>
<|im_start|>assistant
"""

    def __init__(self):
        self.history_public = []
        self.history_private = {}
        self.private = False
        self.container_drink_fee_name = 'nois-drink-fee'
        self.container_client = blob_service_client.get_container_client(self.container_drink_fee_name)
        self.user = {"username":'', "mail":''}

        self.llm = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='gpt-35-turbo-16k',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.5,
            max_tokens=400
        )

        self.llm2 = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='gpt-35-turbo-16k',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.7,
            max_tokens=600
        )

        self.llm3 = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='gpt-35-turbo-16k',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.0,
            max_tokens=600
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

        self.qa_chain = load_qa_with_sources_chain(llm=self.llm, chain_type="stuff", prompt=PromptTemplate.from_template(self.chat_template))
        self.keywordChain = LLMChain(llm=self.llm3, prompt=PromptTemplate.from_template(self.keyword_templ))
        self.classifier_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.classifier_template))
        self.drink_chain = load_qa_with_sources_chain(llm=self.llm2, chain_type="stuff", prompt=PromptTemplate.from_template(self.drink_fee_template))
        self.header_drink_chain = load_qa_with_sources_chain(llm=self.llm2, chain_type="stuff", prompt=PromptTemplate.from_template(self.header_templ_drink_fee))

        # usecase 2
        self.classifier_hrm_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.classifier_hrm))
        #post leave application
        self.leave_application_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.classifier_leave_application))

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
        print(hist)

    def update_token(self, token, email):
        cursor.execute(f"""SELECT token FROM history WHERE email = '{email}';""")
        conv_type = cursor.fetchone()
        print(conv_type)
        token = token.replace("'", "''")

        if not conv_type[0]:
            print(f"Conversation type to be updated to SQL: {token}\n")
            cursor.execute(f"""UPDATE history
                SET token = N'{token}' WHERE email = '{email}';""")
            conn.commit()
            return
        
        print(f"Conversation type to be updated to SQL: {token}\n")
        cursor.execute(f"""UPDATE history
            SET token = N'{token}' WHERE email = '{email}';""")
        conn.commit()
        return
    
    def get_token(self, email):
        cursor.execute(f"""SELECT token FROM history WHERE email = '{email}';""")
        hist = cursor.fetchone()

        if not hist:
            cursor.execute(f"""INSERT INTO history
    VALUES ('{email}', NULL, NULL, NULL, NULL, NULL, NULL);""")
            conn.commit()

            return ''

        if not hist[0]:
            return ''
        
        return hist[0]

    def test_token(self, email):
        tok = self.get_token(email)

        url = "https://api-hrm.nois.vn/api/user/me"
        header = {"Authorization": f"Bearer {tok}"}

        response = requests.get(url, headers=header)
        response.encoding = 'UTF-8'

        if response.status_code == 200:
            return True

        return False

    def chat(self, query, email, name):
        global token
        token = self.get_token(email)
        url = "https://api-hrm.nois.vn/api/user/me"
        header = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=header)
        response.encoding = 'utf-8'

        if response.status_code == 200:
            pass

        else:
            self.update_token(query, email)
            token = self.get_token(email)
            header = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=header)
            response.encoding = 'utf-8'
            
            print(response)
            if response.status_code == 200:
                return "Bạn đã đăng nhập thành công vào HRM.", ''
            else:
                return "Vui lòng nhập lại HRM token", ''

        if self.private:
            # if email not in self.history_private:
            #     self.history_private[email] = []

            return self.chat_private(query, email, name)

        return self.chat_public(query)

    def chat_public(self, query):
        keywords = self.keywordChain({'question': query, 'context': self.get_history_as_txt()})['text']
        print(f"Query: {query}\nKeywords: {keywords}")

        chain = self.qa_chain
        doc = self.get_document(keywords, self.retriever_public)

        try:
            response = response = chain({'input_documents': doc, 'question': query, 'context': self.get_history_as_txt(),
                    'user_info': ''},
                             return_only_outputs=False)
        except Exception as e:
            return {'output_text': f'Cannot generate response, error: {e}'}, doc

        self.add_to_history(query, response['output_text'])
        return response, doc

    def chat_hrm(self, query, email):
        print (self.get_conversation_type(email))
        if self.get_conversation_type(email) == ['','']:
            label_hrm = self.classifier_hrm_chain(query)['text']
        else:
            label_hrm = self.get_conversation_type(email)[0]

        response = """"""
        print(label_hrm)
        if label_hrm == "User":
            response = run_return_user_response(email, query, token)
        elif label_hrm == "LeaveApplication":
            if self.get_conversation_type(email) == ['','']:
                leave_application_type = self.leave_application_chain(query)['text']
            else:
                leave_application_type = self.get_conversation_type(email)[1]

            print(leave_application_type)
            if leave_application_type == 'get':
                response = run_get_leave_application(email, query, token)
            elif leave_application_type == 'post':
                self.update_conversation_type(['LeaveApplication', 'post'], email)
                post_leave_application_response = post_leave_application_func(self.user, query, token, email)
                response = post_leave_application_response[0]
                print(post_leave_application_response)
                try:
                    if post_leave_application_response[1].status_code == 200:
                        self.update_conversation_type(['', ''], email)
                    elif post_leave_application_response[1].status_code == 401:
                        self.update_conversation_type(['', ''], email)
                    elif post_leave_application_response[1].status_code == 100:
                        self.update_conversation_type(['', ''], email)
                except:
                    pass

            elif leave_application_type == 'delete':
                self.update_conversation_type(['LeaveApplication','delete'], email)
                print("delete - pass")
                response = run_leave_application_delete(email, query, "", token)
                if (response =="unrelated response to previous question, cancelled previous action"):
                    self.update_conversation_type(['', ''], email)
                    self.clear_history()
                    return response
                elif (response == "Đã xóa thành công" or response == "empty list"):
                    self.clear_history()
                    self.update_conversation_type(['', ''], email)
        
        return response
    
    def update_conversation_type(self, conversation_type, email):
        cursor.execute(f"""SELECT conversation_type FROM history WHERE email = '{email}';""")
        conv_type = cursor.fetchone()
        print(conv_type)
        res = str(conversation_type).replace("'", "")

        print(res)
        if not conv_type[0]:
            print(f"Conversation type to be updated to SQL: {res}\n")
            cursor.execute(f"""UPDATE history
                SET conversation_type = N'{res}' WHERE email = '{email}';""")
            conn.commit()
            return
        
        print(f"Conversation type to be updated to SQL: {res}\n")
        cursor.execute(f"""UPDATE history
            SET conversation_type = N'{res}' WHERE email = '{email}';""")
        conn.commit()
        return
    
    def get_conversation_type(self, email):
        cursor.execute(f"""SELECT conversation_type FROM history WHERE email = '{email}';""")
        hist = cursor.fetchone()

        if not hist:
            cursor.execute(f"""INSERT INTO history
VALUES ('{email}', NULL, NULL, NULL, NULL, NULL, NULL);""")
            conn.commit()

            return ['','']

        if not hist[0]:
            return ['','']
        
        hist[0] = hist[0].replace("[", "").replace("]", "")
        lst = hist[0].split(",")
        return [s.strip() for s in lst]
    
    def add_to_history_sql(self, query, response, email):
        n = 3
        cursor.execute(f"""SELECT chat FROM history WHERE email = '{email}';""")
        hist = cursor.fetchone()

        if not hist[0]:
            res = f"{query}||{response}".replace("'", "''")

            print(f"History to be updated to SQL: {res}\n")
            cursor.execute(f"""UPDATE history
                SET chat = N'{res}' WHERE email = '{email}';""")
            conn.commit()
            return

        hist = hist[0].split("<sep>")

        hist.append(f"{query}||{response}")
        if len(hist) > n:
            hist = hist[len(hist) - n:]

        res = "<sep>".join(hist).replace("'", "''")
        print(f"History to be updated to SQL: {res}\n")
        cursor.execute(f"""UPDATE history
            SET chat = N'{res}' WHERE email = '{email}';""")
        conn.commit()
        return
    
    def get_history_as_txt_sql(self, email):
        cursor.execute(f"""SELECT chat FROM history WHERE email = '{email}';""")
        hist = cursor.fetchone()

        if not hist:
            cursor.execute(f"""INSERT INTO history
VALUES ('{email}', NULL, NULL, NULL, NULL, NULL, NULL);""")
            conn.commit()

            return ""

        if not hist[0]:
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

        # print(f"History from SQL: {txt}\n")
        return txt

    def chat_private(self, query, email, name):
        print(self.get_conversation_type(email)[0] == 'LeaveApplication')
        
        if str(self.get_conversation_type(email)[0]) == '':
            label = self.classifier_chain({'question': query, 'context': self.get_history_as_txt_sql(email)})['text']
        else:
            label = "hrm"

        print("label " + label)
        keywords = self.keywordChain({'question': query, 'context': self.get_history_as_txt_sql(email)})['text']
        print(keywords)

        chain = self.qa_chain

        if label == "drink fee":
            # self.history_private = []

            # keywordChain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.keyword_templ_drink_fee))
            # keywords_drink_fee = keywordChain({'context': self.get_history_as_txt(), 'question': query})

            doc = self.get_document(keywords, self.retriever_drink)[:1]

            input_pandas = self.drink_chain({'input_documents': doc, 'question': query, 'context': self.get_history_as_txt_sql(email)}, return_only_outputs=False)
            blob_name = doc[0].metadata['metadata_storage_name']
        
            print(input_pandas['output_text']) 
            temp_result = self.excel_drink_preprocess(input_pandas['output_text'], blob_name, doc)
            print(temp_result)
            result_doc = "Input: " + query +"\n Output: " + str(temp_result)
            print(result_doc)

            if """count""" not in input_pandas['output_text']:
                self.add_to_history_sql(query, 'Satisfied Anwser', email)
                return {'output_text': str(temp_result)}, doc
            doc[0].page_content = result_doc

        elif label == "policy":
            doc = self.get_document(keywords, self.retriever_policy)

        elif label == "hrm":
            response = self.chat_hrm(query, email)
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
            response = chain({'input_documents': doc, 'question': query, 'context': self.get_history_as_txt_sql(email),
                                'user_info': f'''The user chatting with you is named {self.user['username']}, with email: {self.user['mail']}. 
                                '''},
                             return_only_outputs=False)

        except Exception as e:
            return {'output_text': f'Cannot generate response, error: {e}'}, doc

        # self.add_to_history(query, response['output_text'])
        self.add_to_history_sql(query, response['output_text'], email)
        return response, doc

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

        sas_i = generate_blob_sas(account_name = account_name,
                            container_name = self.container_drink_fee_name,
                            blob_name = file_name,
                            account_key=account_key,
                            permission=BlobSasPermissions(read=True),
                            expiry=datetime.utcnow() + timedelta(hours=1))

        sas_url = 'https://' + account_name+'.blob.core.windows.net/' + self.container_drink_fee_name + '/' + file_name + '?' + sas_i

        df = pd.read_excel(sas_url)
        doc[0].page_content = df
        header = self.header_drink_chain({'input_documents': doc, 'question': 'What is Header of this file?', 'context': ''}, return_only_outputs=False)
        old_header = list(df.columns)
        header_list = ast.literal_eval(header['output_text'])
        target_rows = df[(df[old_header[0]] == header_list[0]) & (df[old_header[1]] == header_list[1]) & (df[old_header[3]] == header_list[3])]
        df = pd.read_excel(sas_url, skiprows = target_rows.index[0] + 1)
        print(df)

        last_row_index = df.index[df.isnull().all(axis=1)][0]
        df = df.iloc[:last_row_index]
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