from langchain.prompts import PromptTemplate
from langchain.document_transformers import Document
from azure.core.credentials import AzureKeyCredential
from langchain.chains import LLMChain
from azure.search.documents import SearchClient
from langchain.chat_models import AzureChatOpenAI
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

import re

# image processing
from PIL import Image
import urllib.request
import io
from agent import *
from datetime import datetime, timedelta

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

class chatAI:
    chat_template = """<|im_start|>system
Assistant helps the company employees and users with their questions about the companies New Ocean and NOIS. Your answer must adhere to the following criteria:
You must follow this rule:
- If question is in English, answer in English. If question is in Vietnamese, answer in Vietnamese 
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
<|im_end|>

Input: {question}
<|im_start|>assistant
Output:"""

    keyword_leave_application = """<|im_start|>system
Given a sentence and a conversation, assistant will extract keywords based on the conversation and the sentence.
Your output will be on one line, separated by commas. Do not duplicate keywords.
Assume the context is about the companies unless specified otherwise. Only return the keywords, do not output anything else.

EXAMPLE
Input: tôi muốn nghỉ ngày mai vì đi khám bệnh
Output: 'ngày mai','đi khám bệnh'
Input: ngày mốt tôi nghỉ để đi học
Output: 'ngày mốt','đi học'
Input: thứ 5 tuần sau tôi muốn nghỉ về quê
Output: 'thứ 5 tuần sau','về quê'
Input: ngày 3 tháng sau tôi muốn nghỉ để đi công tác
Output: 'ngày 3 tháng sau','đi công tác'
Input: tôi muốn nghỉ 2 ngày, ngày mai và ngày mốt
Output: 'ngày mai và ngày mốt',''
Input: tôi muốn nghỉ 3 ngày, ngày 17,18,19 vì lí do nhà có việc gấp
Output: 'ngày 17,18,19','nhà có việc gấp'
Input: tôi muốn nghỉ từ ngày 24 đến ngày 26
Output: 'từ ngày 24 đến ngày 26',''
Input: tôi muốn nghỉ từ ngày 31 tháng này đến ngày 2 tháng sau do phải đám cưới
Output: 'từ 31 tháng này đến ngày 2 tháng sau','phải đám cưới'
Input: tôi muốn nghỉ từ ngày 8 đến ngày 10 tháng sau vì gặp khách hàng
Output: 'từ ngày 8 đến ngày 10 tháng sau','gặp khách hàng'
Input: tôi muốn nghỉ từ 19/7 đến 21/7
Output: 'từ 19/7 đến 21/7',''
Input: tôi muốn nghỉ từ 4/10 đến 6/10 với lí do về quê
Output: 'từ 4/10 đến 6/10','về quê'
<|im_end|>
{context}
<|im_start|>user
Input: {question}
<|im_end|>
<|im_start|>assistant
Output:"""

    date_determine = """<|im_start|>system
Given a sentence, assistant will determine if the sentence just belongs in 1 of 2 categories, which are:
- yes
- no
You answer the question "The user input has duration lasts for many days?"
EXAMPLE
Input: ngày mai và ngày mốt
Output: yes
Input: ngày mai
Output: no
Input: ngày 17,18,19
Output: yes
Input: ngày mốt
Output: no
Input: thứ 5 tuần sau
Output: no
Input: từ ngày 24 đến ngày 26
Output: yes
Input: ngày 3 tháng sau
Output: no
Input: từ 31 tháng này đến ngày 2 tháng sau
Output: yes
Input: chiều thứ 6 tuần sau
Output: no
Input: từ ngày 8 đến ngày 10 tháng sau
Output: yes
Input: sáng 20/07/2023
Output: no
Input: từ 19/7 đến 21/7
Output: yes
Input: từ thứ hai đến thứ hai
Output: yes
Input: từ 4/10 đến 6/10
Output: yes
Input: từ ngày mai đến ngày mốt
Output: yes

<|im_end|>

Input: {question}
<|im_start|>assistant
Output:"""

    keyword_bANDe = """<|im_start|>system
Given a sentence and a conversation, assistant will extract keywords based on the conversation and the sentence.
Your output will be on one line, separated by commas. Do not duplicate keywords.
Assume the context is about the companies unless specified otherwise. Only return the keywords, do not output anything else.
The first keyword has values of begin date.
The second keyword has values of end date.

EXAMPLE
Input: ngày mai và ngày mốt
Output: 'ngày mai','ngày mốt'
Input: ngày 17,18,19
Output: 'ngày 17','19'
Input: từ ngày 24 đến ngày 26
Output: 'ngày 24','ngày 26'
Input: từ 31 tháng này đến ngày 2 tháng sau
Output: '31 tháng này','ngày 2 tháng sau'
Input: từ ngày 8 đến ngày 10 tháng sau
Output: 'ngày 8','ngày 10 tháng sau'
Input: từ 19/7 đến 21/7
Output: '19/7','21/7'
Input: từ thứ hai đến thứ hai
Output: 'thứ hai','thứ hai'

<|im_end|>
{context}
<|im_start|>user
Input: {question}
<|im_end|>
<|im_start|>assistant
Output:"""

    check_specific_date = """<|im_start|>system
Given a sentence, assistant will determine if the sentence belongs in 1 of 2 categories, which are:
- "yes"
- "no"
You answer the question "Does the input already have date details? (If there is specific date in the input, the output alwways be yes)"
EXAMPLE
Input: ngày 18
Output: yes
Input: thứ 5 2 tuần nữa
Output: no
Input: ngày 21 tháng 6
Output: yes
Input: thứ 5 tuần này
Output: no
Input: 7/9
Output: yes
Input: ngày 12 tháng sau
Output: yes
Input: ngày 30 2 tháng nữa
Output: yes

<|im_end|>

Input: {question}
<|im_start|>assistant
Output:"""

    keyword_specific_weekday = """<|im_start|>system
Given a sentence and a conversation, assistant will extract keywords based on the conversation and the sentence.
Your output will be on two  line, separated by commas. Do not duplicate keywords.
Assume the context is about the companies unless specified otherwise. Only return the keywords, do not output anything else.
Your output will look like:
Date: 0 (2=Monday(thứ 2 or thứ hai), 3=Tuesday(thứ 3 or thứ ba), 4=Wednesday(thứ 4 or thứ tư), 5=Thusday(thứ 5 or thứ năm), 6=Friday(thứ 6 or thứ sáu), 7=Saturday(thứ 7 or thứ bảy), 8=Sunday(chủ nhật))
Week: 0 (default = 0) (next week = 1, 2 weeks later = 2, etc.)

EXAMPLE
Input: thứ 5 tuần sau
Output: Date: 5
Week: 1

Input: thứ năm 2 tuần nữa
Output: Date: 5
Week: 2

Input: thứ ba tuần này
Output: Date: 3
Week: 0

<|im_end|>
{context}
<|im_start|>user
Input: {question}
<|im_end|>
<|im_start|>assistant
Output:"""

    keyword_specific_date = """<|im_start|>system
Given a sentence and a conversation, assistant will extract keywords based on the conversation and the sentence.
Your output will be on three line, separated by commas. Do not duplicate keywords.
Assume the context is about the companies unless specified otherwise. Only return the keywords, do not output anything else.
Your output will look like:
Date: 0 (default = 0)
Month: 0 (default = 0) (next month (tháng sau) = +1, 2 months later (2 tháng sau) = +2, etc.) (if month in the future, add '+' before number of month)
Year: 0 (default = 0) (if the input contains the last 2 digits of the year, add '20' at the beginning of the year)

EXAMPLE
Input: ngày 23 tháng 8
Output: Date: 23
Month: 8
Year: 0

Input: ngày 16
Output: Date: 16
Month: 0
Year: 0

Input: 12-12-23
Output: Date: 12
Month: 12
Year: 2023

Input: ngày 30 tháng sau
Output: Date: 31
Month: +1
Year: 0

Input: ngày 3 2 tháng sau
Output: Date: 3
Month: +2
Year: 0

Input: 31/10/2024
Output: Date: 31
Month: 10
Year: 2024

<|im_end|>
{context}
<|im_start|>user
Input: {question}
<|im_end|>
<|im_start|>assistant
Output:"""

    def __init__(self):
        self.use_agent = False
        self.agent = Agent()

        self.history_hrm = []
        self.today_var = datetime.now().date()
        self.user = {"username":' ', "mail":' '}
        self.leave_application_form = {
            'start_date': '',
            'end_date': '',
            'duration': 0,
            'note': ''
        }

        self.llm = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='gpt-35-turbo-16k',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.5,
            max_tokens=2000
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

        #general
        self.qa_chain = load_qa_with_sources_chain(llm=self.llm, chain_type="stuff", prompt=PromptTemplate.from_template(self.chat_template))
        self.classifier_hrm_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.classifier_hrm))

        #post leave application
        self.leave_application_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.classifier_leave_application))
        self.chain_leave_application = LLMChain(llm=self.llm3, prompt=PromptTemplate.from_template(self.keyword_leave_application))
        self.date_determine_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.date_determine))
        self.chain_bANDe= LLMChain(llm=self.llm3, prompt=PromptTemplate.from_template(self.keyword_bANDe))

        #function check specific date
        specific_date_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.check_specific_date))
        chain_specific_weekday = LLMChain(llm=self.llm3, prompt=PromptTemplate.from_template(self.keyword_specific_weekday))
        chain_specific_date = LLMChain(llm=self.llm3, prompt=PromptTemplate.from_template(self.keyword_specific_date))

    def chat(self, query):
        return self.chat_hrm(query)

    def toggle_agent1(self):
        if self.use_agent:
            self.use_agent = False
            return "Disabled agent."

        else:
            self.use_agent = True
            return "Enabled agent."

    def chat_hrm(self, query):
        label = self.classifier_hrm_chain(query)['text']  
        response = """"""
        try:
            if label == "User":
                response = label
            elif label == "LeaveApplication":
                leave_application_type = self.leave_application_chain(query)['text']
                if leave_application_type == 'get':
                    pass
                elif leave_application_type == 'post':
                    keywords = self.chain_leave_application({'question': query, 'context':''})['text']
                    values_keywords = keywords.split(",")
                    time = values_keywords[0].strip("'")
                    note = values_keywords[1].strip("'")
                    self.leave_application_form['note'] = note
                    
                    if self.date_determine_chain(time)['text'] == "yes":
                        keywords_bANDe = self.chain_bANDe({'question': query, 'context':''})['text']
                        response = keywords_bANDe
                        values_keywords_bANDe = keywords_bANDe.split(",")
                        begin_date = values_keywords_bANDe[0].strip("'")
                        end_date = values_keywords_bANDe[1].strip("'")
                        self.leave_application_form['start_date'] = self.date_processing(begin_date)
                        self.leave_application_form['end_date'] = self.date_processing(end_date)
                        response = str(self.leave_application_form)
                    else:
                        pass


        except Exception as e:
            return {'output_text': f'Cannot generate response, error: {e}'}, 'Thien'

        self.add_to_history(query, response)         
        return response

    def date_processing(self, date_off):
        if "mai" in date_off:
            day_after_next = self.today_var + timedelta(days=1)
            return day_after_next.strftime("%m/%d/%Y")
        elif "mốt" in date_off:
            day_after_next = self.today_var + timedelta(days=2)
            return day_after_next.strftime("%m/%d/%Y")
        else:
            if 'no' in self.specific_date_chain(date_off)['text']:
                keywords = self.chain_specific_weekday({'question': date_off, 'context':''})['text']
                lines = keywords.split("\n")

                # Extract the values of date and week from the list of lines
                date = int(lines[0].split(": ")[1]) - 2
                if (self.today_var.weekday() - date <= 0):
                    week = int(lines[1].split(": ")[1])
                else:
                    week = int(lines[1].split(": ")[1]) - 1

                # Calculate the number of days until Monday (0 = Monday, 1 = Tuesday, etc.)
                weekday = (date - self.today_var.weekday()) % 7
                # Calculate the date of the next Monday
                next_weekday = self.today_var + timedelta(days=weekday)
                next_week = next_weekday + timedelta(weeks=week)
                return next_week.strftime("%m/%d/%Y")
            else:
                keywords = self.chain_specific_date({'question': date_off, 'context':''})['text']
                lines = keywords.split("\n")

                # Extract the integer values of date, month, and year
                date = int(lines[0].split(': ')[1])
                if int(lines[2].split(': ')[1]) == 0:
                    year = self.today_var.year
                else:
                    year = int(lines[2].split(': ')[1])

                if '+' in lines[1]:
                    month_str = lines[1].split(': ')[1].strip().replace('+', '')
                    month = int(month_str) - 1
                    # Calculate the date of the 15th day of the month after next
                    day_of_month_after_next = datetime(year + ((self.today_var.month + month) // 12), ((self.today_var.month + month) % 12) + 1, date)
                    return day_of_month_after_next.strftime("%m/%d/%Y")
                else:
                    if int(lines[1].split(': ')[1]) == 0:
                        month = self.today_var.month
                    else:
                        month = int(lines[1].split(': ')[1])
                    day_of_month_after_next = datetime(year, month, date)
                    return day_of_month_after_next.strftime("%m/%d/%Y")


    def get_history_as_txt(self, n=3):
        txt = ""
        hist = self.history_hrm

        if len(hist) <= n:
            history = hist

        else:
            history = hist[len(hist) - n:]

        for i in history:
            txt += f"\n<|im_start|>user\n{i['user']}\n<|im_end|>\n"
            txt += f"<|im_start|>assistant\n{i['AI']}\n<|im_end|>"

        return txt

    def add_to_history(self, user_msg, ai_msg):
        hist = self.history_hrm

        hist.append({'user': user_msg, 'AI': ai_msg})

    def clear_history(self):
        self.history_hrm = []

    def clear_agent_history(self):
        self.agent.history1.clear()
        self.agent.history2.clear()
        return "Cleared agent's history."
