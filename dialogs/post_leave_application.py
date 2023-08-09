from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.chains import LLMChain
from langchain.chat_models import AzureChatOpenAI
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from datetime import datetime, timedelta
from unidecode import unidecode

import requests
import numpy as np
import ast
import pyodbc

"""Connect to SQL """

url = "https://api-hrm.nois.vn/api"

server = 'sql-chatbot-server.database.windows.net'
database = 'sql-chatbot'
username = 'test-chatbot'
password = 'bMp{]nzt1'
driver= '{ODBC Driver 17 for SQL Server}'

conn = pyodbc.connect(f'DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}')
cursor = conn.cursor()


"""
    Load Large Model Language of Azure Open AI
    llm: using for generating final output
    llm2: using for generating output
    llm3: using for getting keyword
"""

llm = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='gpt-35-turbo-16k',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.5,
            max_tokens=2000
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
    temperature=0.0,
    max_tokens=600
)

"""prompt for getting keyword 'time' and 'cause' of leave application"""

keyword_leave_application = """<|im_start|>system
Given a sentence and a conversation, assistant will extract keywords based on the conversation and the sentence.
Your output will be on one line, separated by commas. Do not duplicate keywords.
Assume the context is about the companies unless specified otherwise. Only return the keywords, do not output anything else.
Output MUST JUST have 2 data fields: 'time', 'cause'. If any field is missing, the value of that data field is ''
Field 'time': time for leave application
Field 'cause': reason for leave application, not related to changing requirement or type of leave application.

EXAMPLE
Input: buổi sáng
Output: 'sáng',''
Input: buổi chiều
Output: 'chiều',''
Input: nguyên ngày
Output: 'cả nyày',''
Input: với lí do đi công tác
Output: '','đi công tác'
Input: lí do là "test"
Output: '','test'
Input: nhà có việc gấp
Output: '','nhà có việc gấp'
Input: tôi muốn đổi lí do thành đi học
Output: '','đi học'
Input: hình thức nghỉ là nghỉ không lương
Output: '',''
Input: hình thức nghỉ là nghỉ ốm
Output: '',''
Input: hình thức nghỉ là nghỉ bhxh
Output: '',''
Input: hình thức nghỉ là nghỉ công tác
Output: '',''
Input: tôi muốn sửa ngày phép thành thứ 5 đến thứ 6 tuần này
Output: 'thứ 5 đến thứ 6 tuần này',''
Input: tôi muốn đổi thày chiều mai
Output: 'chiều mai','''
Input: tôi muốn đổi buổi nghỉ thành buổi chiều
Output: 'buổi chiều','đi học'
Input: vì phải đi đám cưới
Output: '','phải đi đám cưới'
Input: tôi muốn nghỉ ngày mai cả ngày vì đi khám bệnh
Output: 'ngày mai cả ngày','đi khám bệnh'
Input: nguyên ngày mốt tôi nghỉ để đi học
Output: 'nguyên ngày mốt','đi học'
Input: thứ 5 tuần sau tôi muốn nghỉ về quê
Output: 'thứ 5 tuần sau','về quê'
Input: cả ngày 3 tháng sau tôi muốn nghỉ để đi công tác
Output: 'cả ngày 3 tháng sau','đi công tác'
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

"""prompt for getting keyword 'name of manager' of leave application"""

keyword_name_manager = """<|im_start|>system
Given a sentence and a conversation, assistant will extract keywords based on the conversation and the sentence.
Your output will be on one line, separated by commas. Do not duplicate keywords.
Assume the context is about the companies unless specified otherwise. Only return the keywords, do not output anything else.
Output MUST JUST have 1 data fields: 'name of manager'. If any field is missing, the value of that data field is ''.
Output will return name of manager. If in the input not have name of manager. The output just is ''.

EXAMPLE
Input: Nguyễn Thị Mỹ Dung
Output: 'Nguyễn Thị Mỹ Dung'
Input: người quản lý của tôi là chị TRẦN THỊ THÚY AN
Output: 'TRẦN THỊ THÚY AN'
Input: tôi muốn nghỉ ngày mai với lí do đi học, người duyệt đơn tôi là anh Ninh
Output: 'Ninh'
Input: chị ĐỔNG HỒNG NHUNG sẽ duyệt đơn tôi
Output: 'ĐỔNG HỒNG NHUNG'
Input: sẽ được duyệt bởi TRẦN VĂN KHANG
Output: 'TRẦN VĂN KHANG'
Input: anh quân sẽ là người duyệt đơn tôi
Output: 'quân'
Input: tài sẽ duyệt đơn tôi
Output: 'tài'
Input: PHẠM THỊ DIỄM PHÚC
Output: 'PHẠM THỊ DIỄM PHÚC'
Input: ngày mai tôi sẽ đi họp
Output: ''
Input: Tai Vo sẽ duyệt đơn tôi
Output: 'Tai Vo'

<|im_end|>
{context}
<|im_start|>user
Input: {question}
<|im_end|>
<|im_start|>assistant
Output:"""


"""prompt for getting keyword 'leave type' of leave application"""

keyword_leave_type = """<|im_start|>system
Given a sentence and a conversation, assistant will extract keywords based on the conversation and the sentence.
Your output will be on one line, separated by commas. Do not duplicate keywords.
Assume the context is about the companies unless specified otherwise. Only return the keywords, do not output anything else.
Output MUST JUST have 1 data fields: 'leave type'. If any field is missing, the value of that data field is ''.
Output will return name of manager. If in the input not have name of manager. The output just is ''.

EXAMPLE
Input: tôi nghỉ ngày mai để đi học
Output: ''
Input: tôi nghỉ ngày mai để đi học hình thức nghỉ là nghỉ không lương
Output: 'nghỉ không lương'
Input: hình thức nghỉ là nghỉ có lương
Output: 'nghỉ có lương'
Input: nghỉ ốm
Output: 'nghỉ ốm'
Input: hình thức nghỉ bảo hiểm xã hội
Output: 'nghỉ bảo hiểm xã hội'
Input: hình thức nghỉ hưởng BHXH
Output: 'nghỉ hưởng BHXH'
Input: hình thức nghỉ là Nghỉ hội nghị
Output: 'Nghỉ hội nghị'
Input: hình thức nghỉ Nghỉ hội nghị, đào tạo
Output: 'Nghỉ hội nghị, đào tạo'
Input: hình thức nghỉ Nghỉ khác
Output: 'Nghỉ khác'

<|im_end|>
{context}
<|im_start|>user
Input: {question}
<|im_end|>
<|im_start|>assistant
Output:"""


"""prompt for getting keyword '' of leave application"""

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
Input: từ thứ 5 đến thứ 6
Output: yes

<|im_end|>

Input: {question}
<|im_start|>assistant
Output:"""

"""prompt for getting keyword 'leave application' of leave application"""

keyword_bANDe = """<|im_start|>system
Given a sentence and a conversation, assistant will extract keywords based on the conversation and the sentence.
Your output will be on one line, separated by commas. Do not duplicate keywords.
Assume the context is about the companies unless specified otherwise. Only return the keywords, do not output anything else.
You should note that: "tomorrow" and "the day after tomorrow" are 2 different days
The first keyword has values of begin date.
The second keyword has values of end date.

EXAMPLE
Input: ngày mai và ngày mốt
Output: 'ngày mai','ngày mốt'
Input: mai và mốt
Output: 'mai','mốt'
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
Input: từ thứ 5 đến thứ 6
Output: 'thứ 5','thứ 6'

<|im_end|>
{context}
<|im_start|>user
Input: {question}
<|im_end|>
<|im_start|>assistant
Output:"""

"""prompt for checking the input already have date details"""

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


"""prompt for getting keyword of specific weekday"""

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


"""prompt for getting keyword of specific date"""

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

"""prompt for generate final output"""

chat_template = """<|im_start|>system
Assistant helps the company employees. Your answer must adhere to the following criteria:
You must follow this rule:
- Answer in Vietnamese 
- Be brief but friendly in your answers. You may use the provided sources to help answer the question. If there isn't enough information, say you don't know. If asking a clarifying question to the user would help, ask the question.
- If the user greets you, respond accordingly.
- If there is full information in the dataset, Your output will thank the application and ask the user if there are any additional services to use

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


"""prompt for generate keyword session"""
keyword_session = """<|im_start|>system
Given a sentence and a conversation, assistant will extract keywords based on the conversation and the sentence.
Your output will be on one line, separated by commas. Do not duplicate keywords.
Assume the context is about the companies unless specified otherwise. Only return the keywords, do not output anything else.
Output must have 2 data fields: 'session', 'date'. If any field is missing, the value of that data field is ''

The first keyword has only values: '', 'sáng', 'chiều', 'cả ngày'
If there is not any value of date, the second keyword has values: '','ngày mai','ngày mốt',...
In Vietnamese, "all day" means "cả ngày", "nguyên ngày" or "từ sáng đến chiều". So if have any string like "cả ngày", "nguyên ngày" or "từ sáng đến chiều" in the input, the first keyword has value 'cả ngày'

EXAMPLE
Input: buổi 
Output: '',''
Input: buổi sáng
Output: 'sáng',''
Input: buổi chiều
Output: 'chiều',''
Input: nguyên ngày
Output: 'cả nyày',''
Input: ngày mai
Output: '','ngày mai'
Input: mai
Output: '','mai'
Input: mốt
Output: '','mốt'
Input: nguyên ngày mốt
Output: 'cả ngày', 'ngày mốt'
Input: thứ 5 tuần sau
Output: '','thứ 5 tuần sau'
Input: sáng mai
Output: 'sáng','mai'
Input: chiều nay
Output: 'sáng','nay'
Input: chiều thứ 6 tuần sau
Output: 'chiều','thứ 6 tuần sau'
Input: cả ngày thứ 3 2 tuần nữa tuần sau
Output: 'cả ngày','thứ 3 2 tuần nữa tuần sau'
Input: sáng 20/07/2023
Output: 'sáng','20/07/2023'
Input: chiều ngày 3 tháng sau
Output: 'chiều','ngày 3 tháng sau'
Input: thứ 2 cả ngày 
Output: 'cả ngày','thứ 2'


<|im_end|>
{context}
<|im_start|>user
Input: {question}
<|im_end|>
<|im_start|>assistant
Output:"""


"""prompt for checking the answer is yes, no or neutral"""
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


"""Crete chain for each prompt"""
chain_leave_application = LLMChain(llm=llm3, prompt=PromptTemplate.from_template(keyword_leave_application))
chain_name_manager = LLMChain(llm=llm3, prompt=PromptTemplate.from_template(keyword_name_manager))
chain_leave_type = LLMChain(llm=llm3, prompt=PromptTemplate.from_template(keyword_leave_type))

date_determine_chain = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(date_determine))
chain_bANDe= LLMChain(llm=llm3, prompt=PromptTemplate.from_template(keyword_bANDe))
specific_date_chain = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(check_specific_date))
chain_specific_weekday = LLMChain(llm=llm3, prompt=PromptTemplate.from_template(keyword_specific_weekday))
chain_specific_date = LLMChain(llm=llm3, prompt=PromptTemplate.from_template(keyword_specific_date))
qa_chain = load_qa_with_sources_chain(llm=llm, chain_type="stuff", prompt=PromptTemplate.from_template(chat_template))
chain_session = LLMChain(llm=llm3, prompt=PromptTemplate.from_template(keyword_session))
confirm_chain = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(confirm_template))

#getting today
today_var = datetime.now().date()
leave_application_form = {
            'start_date': ' ',
            'end_date': ' ',
            'duration': 0,
            'note': ' ',
            'periodType': -1,
            'reviewUser': 0,
            'leaveType': -1,
        }

confirm_delete = False


"""
    Input: 
        leave_application_form: include label of conversasion and type of API. for example: ['LeaveApplication', 'post']
        email: email of the user
    Output:
        return
    Purpose:
        update post leave application form in sql server
"""
def update_post_leave(leave_application_form, email):
    cursor.execute(f"""SELECT post_leave FROM history WHERE email = '{email}';""")
    conv_type = cursor.fetchone()
    leave_application_form_str = str(leave_application_form)
    post_leave = leave_application_form_str.replace("'", "''")

    if not conv_type[0]:
        # # print(f"Post leave application form to be updated to SQL: {post_leave}\n")
        cursor.execute(f"""UPDATE history
            SET post_leave = N'{post_leave}' WHERE email = '{email}';""")
        conn.commit()
        return
    
    # # print(f"Post leave application form to be updated to SQL: {post_leave}\n")
    cursor.execute(f"""UPDATE history
        SET post_leave = N'{post_leave}' WHERE email = '{email}';""")
    conn.commit()
    return


"""
    Input: 
        token: token of HRM login
    Output:
        return success or not
    Purpose:
        get leave type of the user(nghỉ có lương, không lương,...)
"""

def get_leave_type_list(token):
    header = {
                "Authorization": f"Bearer {token}"
            }
    url = "https://api-hrm.nois.vn/api/user/dayoff-data"
    response = requests.get(url, headers=header)

    if response.status_code == 200:
        data = response.json()['data']
        return extract_ids(data)
        
    else:
        return "not successful return get_leave_application"
    

"""
    Input: 
       data: list of number of leave type
    Output:
        ids: list of string of leave type
    Purpose:
       extract id of leave type to string of leave type
"""

def extract_ids(data):
    ids = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'id':
                ids.append(value)
            else:
                ids.extend(extract_ids(value))
    elif isinstance(data, list):
        for item in data:
            ids.extend(extract_ids(item))
    return ids



"""
    Input: 
       email: email of user
    Output:
        leave_application_form
    Purpose:
       getting leave application form form sql database
"""
def get_post_leave(email):
    cursor.execute(f"""SELECT post_leave FROM history WHERE email = '{email}';""")
    hist = cursor.fetchone()

    if not hist:
        cursor.execute(f"""INSERT INTO history
VALUES ('{email}', NULL, NULL, NULL, NULL, NULL, NULL, NULL);""")
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


"""
    Input: 
        user: name of user
        query: input from user
        token: token of HRM
        email: email of user
    Output:
        [response,response_data]
        respone: response to user
        response_data: status from HRM server when sending a request
    Purpose:
       post a leave application to HRM
"""
def post_leave_application_func(user, query, token, email):
    try:
        global leave_application_form
        global confirm_delete

        leave_application_form = get_post_leave(email)
        # # print(leave_application_form)
        
        response_data = requests.models.Response()
        response_data.status_code = 0
        reviewUser_string = ''
        leaveType_string = ''
        periodType = ''
        
        if leave_application_form['periodType'] == 0:
                periodType = "Cả ngày"
        elif leave_application_form['periodType'] == 1:
            periodType = "Buổi sáng"
        elif leave_application_form['periodType'] == 2:
            periodType = "Buổi chiều"

        confirm = confirm_chain(query)['text']
        # print(confirm)

        if 'es' in confirm and confirm_delete:
            reviewUser_string = ''
            leaveType_string = ''

            url_leaveapplication = "https://api-hrm.nois.vn/api/leaveapplication"
            data = {
                "reviewUserId": leave_application_form['reviewUser'],
                "relatedUserId": "",
                "fromDate": datetime.strptime(leave_application_form['start_date'], '%Y-%m-%d').strftime('%m/%d/%Y'),
                "toDate": datetime.strptime(leave_application_form['end_date'], '%Y-%m-%d').strftime('%m/%d/%Y'),
                "leaveApplicationTypeId": leave_application_form['leaveType'],
                "leaveApplicationNote": leave_application_form['note'],
                # "numberOffDay": leave_application_form['duration']
                "periodType": leave_application_form['periodType']
            }

            headers = {
                "Authorization": f"Bearer {token}"
            }

            # Make the request
            response_data = requests.post(url_leaveapplication, json=data, headers=headers)

            # print(response_data.status_code)

            leave_application_form = {
                'start_date': ' ',
                'end_date': ' ',
                'duration': 0,
                'note': ' ',
                'periodType': -1,
                'reviewUser': 0,
                'leaveType': -1,
            }

            update_post_leave(leave_application_form, email)

            response = f"""Đã cung cấp đủ thông tin. Đơn sẽ sớm được duyệt. Cảm ơn bạn đã gửi form.
            Bạn có cần tôi giúp đỡ gì thêm không ạ?"""
            return [response,response_data]

        elif 'o' in confirm and confirm_delete:
            leave_application_form = {
                'start_date': ' ',
                'end_date': ' ',
                'duration': 0,
                'note': ' ',
                'periodType': -1,
                'reviewUser': 0,
                'leaveType': -1,
            }

            update_post_leave(leave_application_form, email)

            response_data.status_code = 100
            response = f"""Đơn nghỉ phép của bạn đã xóa. Bạn có thể gửi một Đơn nghỉ phép khác."""
            confirm_delete = False
            return [response,response_data]
            
        # elif 'no' in confirm:
        #     response = f"""Bạn không muốn giữ Đơn nghỉ phép này nữa hả?"""
        #     confirm_delete = True
        #     return [response,response_data]
        else:
            pass

        
        reviewUser = chain_name_manager({'question': query, 'context':''})['text']

        if reviewUser:
            reviewUser_text = unidecode(reviewUser).lower()
            query = query.replace(reviewUser, "")
            if "dung" in reviewUser_text:
                reviewUser_string = 'Nguyễn Thị Mỹ Dung'
                leave_application_form['reviewUser'] = 56
            elif "sang" in reviewUser_text:
                reviewUser_string = 'ĐÀO MINH SÁNG'
                leave_application_form['reviewUser'] = 108
            elif "khang" in reviewUser_text:
                reviewUser_string = 'TRẦN VĂN KHANG'
                leave_application_form['reviewUser'] = 137
            elif "ninh" in reviewUser_text:
                reviewUser_string = 'Trần Đăng Ninh'
                leave_application_form['reviewUser'] = 119
            elif "phuc" in reviewUser_text:
                reviewUser_string = 'PHẠM THỊ DIỄM PHÚC'
                leave_application_form['reviewUser'] = 281
            elif "quan" in reviewUser_text:
                reviewUser_string = 'LÝ MINH QUÂN'
                leave_application_form['reviewUser'] = 139
            elif "nhung" in reviewUser_text:
                reviewUser_string = 'ĐỔNG HỒNG NHUNG'
                leave_application_form['reviewUser'] = 124
            elif "tan" in reviewUser_text:
                reviewUser_string = 'VÕ TẤN TÀI'
                leave_application_form['reviewUser'] = 141
            elif "tai" in reviewUser_text:
                reviewUser_string = 'Tai Vo'
                leave_application_form['reviewUser'] = 298
            elif "an" in reviewUser_text:
                reviewUser_string = 'TRẦN THỊ THÚY AN'
                leave_application_form['reviewUser'] = 95
            else:
                reviewUser_string = ' '


        leaveType = chain_leave_type({'question': query, 'context':''})['text']

        if leaveType:
            query = query.replace(leaveType, "")
            leaveType_text = unidecode(leaveType).lower()
            # print(leaveType_text)
            
            if "phep" in leaveType_text or "co" in leaveType_text:
                leave_application_form['leaveType'] = 1
            elif "khong" in leaveType_text:
                leave_application_form['leaveType'] = 2
            elif "khac" in leaveType_text:
                leave_application_form['leaveType'] = 3
            elif "hoi" in leaveType_text or "dao" in leaveType_text:
                leave_application_form['leaveType'] = 5
            elif "om" in leaveType_text:
                leave_application_form['leaveType'] = 8
            elif "bhxh" in leaveType_text or "bao hiem" in leaveType_text:
                leave_application_form['leaveType'] = 9
            else:
                pass

        # print("leave_application_form['leaveType']:", leave_application_form['leaveType'])
        # print("query:", query)

        
        keywords = chain_leave_application({'question': query, 'context':''})['text']
        values_keywords = keywords.split(",")
        time = values_keywords[0].strip("'")
        note = values_keywords[1].strip("'")
        if note:
            leave_application_form['note'] = note
        
        # print("time", time)
        # print("note", note)

        try:
            if time:
                # print(date_determine_chain(time)['text'])
                if "es" in date_determine_chain(time)['text']:
                    keywords_bANDe = chain_bANDe({'question': query, 'context':''})['text']
                    # response = keywords_bANDe
                    values_keywords_bANDe = keywords_bANDe.split(",")
                    begin_date = values_keywords_bANDe[0].strip("'")
                    end_date = values_keywords_bANDe[1].strip("'")
                    # print("begin_date", begin_date)
                    # print("end_date", end_date)
                    if begin_date:
                        leave_application_form['start_date'] = date_processing(begin_date)
                    if end_date:
                        leave_application_form['end_date'] = date_processing(end_date)

                    leave_application_form['duration'] = int(np.busday_count(leave_application_form['start_date'], leave_application_form['end_date'])) + 1
                    leave_application_form['periodType'] = 0

                    # response = str(leave_application_form)
                else:
                    session_keywords = chain_session({'question': time, 'context':''})['text']
                    # Split the string into a list using the comma as a delimiter
                    split_string_session_keywords = session_keywords.split(",")
                    session_off = split_string_session_keywords[0].strip("'")
                    date_off = split_string_session_keywords[1].strip("'")
                    # print(split_string_session_keywords)
                    # print(date_off)
                    # print(session_off)
                    if date_off:
                        leave_application_form['start_date'] = date_processing(date_off)
                        leave_application_form['end_date'] = leave_application_form['start_date']
                    if session_off == 'sáng':
                        leave_application_form['periodType'] = 1
                        leave_application_form['duration'] = 0.5
                    elif session_off == 'chiều':
                        leave_application_form['periodType'] = 2
                        leave_application_form['duration'] = 0.5
                    elif session_off == 'cả ngày':
                        leave_application_form['periodType'] = 0
                        leave_application_form['duration'] = 1
        except:
            pass

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

        leave_application_form_string = ''

        if leave_application_form == get_post_leave(email):
            response =  f"""Hiện bạn đang có một Form submit ngày nghỉ chưa submit:\n
            ______________________________________________________________________
            Ngày gửi đơn: {today_var}
            Người duyệt: {reviewUser_string}
            Ngày bắt đầu nghỉ: {leave_application_form['start_date']}
            Ngày kết thúc nghỉ: {leave_application_form['end_date']}
            Nghỉ buổi: {periodType}
            Tổng thời gian nghỉ: {leave_application_form['duration']}
            Hình thứ nghỉ: {leaveType_string}
            Lí do: {leave_application_form['note']}    
            ______________________________________________________________________\n
            
            Bạn có muốn giữ đơn nghỉ phép này không? Nếu có thì vui lòng bạn cung cấp những thông tin còn thiếu."""

            confirm_delete = True
        
            return [response,response_data]
        
        if leave_application_form['start_date'] != ' ' or leave_application_form['end_date'] != ' ':
            if datetime.strptime(leave_application_form['start_date'], '%Y-%m-%d').weekday() == 5 or datetime.strptime(leave_application_form['start_date'], '%Y-%m-%d').weekday() == 6:
                leave_application_form['start_date'] = ' '
                leave_application_form_string += 'Hiện tại ngày bạn muốn submit nghỉ' + leave_application_form['start_date'] + 'là ngày cuối tuần. Bạn có thể kiểm tra lại ngày bạn muốn submit được không? Vì ngày bạn muốn nghỉ là ngày cuối tuần.'
            if datetime.strptime(leave_application_form['end_date'], '%Y-%m-%d').weekday() == 5 or datetime.strptime(leave_application_form['end_date'], '%Y-%m-%d').weekday() == 6:
                leave_application_form['end_date'] = ' '
                leave_application_form_string += 'Hiện tại ngày bạn muốn submit nghỉ' + leave_application_form['end_date'] + 'là ngày cuối tuần. Bạn có thể kiểm tra lại ngày bạn muốn submit được không? Vì ngày bạn muốn nghỉ là ngày cuối tuần.'
        # if leave_application_form['start_date'] == ' ' and leave_application_form['end_date'] == ' ':
        if leave_application_form['start_date'] == ' ':
            leave_application_form_string += 'Chưa cung cấp ngày bắt đầu nghỉ.'
        if leave_application_form['end_date'] == ' ':
            leave_application_form_string += 'Chưa cung cấp ngày kết thúc nghỉ.'
        if leave_application_form['note'] == ' ':
            leave_application_form_string += 'Chưa cung cấp nguyên nhân nghỉ.'
        if leave_application_form['periodType'] == -1:
            leave_application_form_string += 'Chưa cung cấp buổi nghỉ(sáng, chiều hay cả ngày).'
        if reviewUser_string == 'unknown':
            leave_application_form_string += 'Nhập sai tên người quản lí. Kiểm tra lại.'
        if leave_application_form['reviewUser'] == 0:
            leave_application_form_string += 'Chưa cung cấp tến người quản lí.'
        # print(leave_application_form['leaveType'], type(leave_application_form['leaveType']), get_leave_type_list(token))
        if leave_application_form['leaveType'] == -1:
            leave_application_form_string += 'Chưa cung cấp hình thức nghỉ.'
        elif str(leave_application_form['leaveType']) in get_leave_type_list(token):
            leave_type_mapping = {
                1: 'Nghỉ phép có lương',
                2: 'Nghỉ không lương',
                8: 'Nghỉ ốm',
                9: 'Nghỉ bảo hiểm xã hội',
                5: 'Nghỉ hội nghị, đào tạo',
                3: 'Nghỉ khác (đám cưới,...)'
            }

            leave_types = get_leave_type_list(token)
            leave_type_strings = [leave_type_mapping.get(leave_type) for leave_type in leave_types]
            string_output = '\n'.join([f'{index + 1}. {leave_type}' for index, leave_type in enumerate(leave_type_strings)])

            response = 'Hiện tại bạn không có loại nghỉ phép ' +  leaveType_string + "Vui lòng bạn nhập lại hình thức nghỉ. Bạn chỉ có thể submit nghỉ phép dưới các hình thức sau đây: \n" + string_output

            return [response, response_data]

        # print(leave_application_form_string)
        update_post_leave(leave_application_form, email)

        

        if leave_application_form_string == '':
            if leave_application_form['periodType'] == 0:
                periodType = "Cả ngày"
            elif leave_application_form['periodType'] == 1:
                periodType = "Buổi sáng"
            elif leave_application_form['periodType'] == 2:
                periodType = "Buổi chiều"
            # viewUser_string = "LÝ MINH QUÂN"


            response = f"""Form submit ngày nghỉ của bạn:\n
            ______________________________________________________________________
            Ngày gửi đơn: {today_var}
            Người duyệt: {reviewUser_string}
            Ngày bắt đầu nghỉ: {leave_application_form['start_date']}
            Ngày kết thúc nghỉ: {leave_application_form['end_date']}
            Nghỉ buổi: {periodType}
            Tổng thời gian nghỉ: {leave_application_form['duration']}
            Hình thứ nghỉ: {leaveType_string}
            Lí do: {leave_application_form['note']}    
            ______________________________________________________________________\n
            
            Bạn có muốn submit đơn nghỉ phép này không?"""

            confirm_delete = True
            
        else:
            result_doc = "Input: " + "Quản lý, còn thiếu thông tin gì về Đơn nghỉ phép nữa không." +"\n Output: Chỉ tập trung trả lời yêu cầu nhân viên cung cấp những yêu cầu chưa cung cấp :" + leave_application_form_string
            doc = [Document(page_content= result_doc,
                                    metadata={'@search.score': 0,
                                            'metadata_storage_name': 'local-source', 'source': f'doc-0'})]

            response = qa_chain({'input_documents': doc, 'question': query, 'context': '',
                                    'user_info': f'''The user chatting with you is named {user['username']}, with email: {user['mail']}. 
                                    '''},
                                return_only_outputs=False)['output_text']
            
        return [response,response_data]
    except Exception as e:
        print(e)
    

def date_processing(date_off):
    # print('date_off', date_off)
    if "nay" in date_off:
        day_after_next = today_var
        return day_after_next.strftime("%Y-%m-%d")
    elif "mai" in date_off:
        day_after_next = today_var + timedelta(days=1)
        return day_after_next.strftime("%Y-%m-%d")
    elif "mốt" in date_off:
        day_after_next = today_var + timedelta(days=2)
        return day_after_next.strftime("%Y-%m-%d")
    else:
        if 'no' in specific_date_chain(date_off)['text']:
            keywords = chain_specific_weekday({'question': date_off, 'context':''})['text']
            lines = keywords.split("\n")

            # Extract the values of date and week from the list of lines
            date = int(lines[0].split(": ")[1]) - 2
            if (today_var.weekday() - date <= 0):
                week = int(lines[1].split(": ")[1])
            else:
                week = int(lines[1].split(": ")[1]) - 1

            # Calculate the number of days until Monday (0 = Monday, 1 = Tuesday, etc.)
            weekday  = (date - today_var.weekday()) % 7
            # Calculate the date of the next Monday
            next_weekday = today_var + timedelta(days=weekday)
            next_week = next_weekday + timedelta(weeks=week)
            return next_week.strftime("%Y-%m-%d")
        else:
            keywords = chain_specific_date({'question': date_off, 'context':''})['text']
            lines = keywords.split("\n")

            # Extract the integer values of date, month, and year
            date = int(lines[0].split(': ')[1])
            if int(lines[2].split(': ')[1]) == 0:
                year = today_var.year
            else:
                year = int(lines[2].split(': ')[1])

            if '+' in lines[1]:
                month_str = lines[1].split(': ')[1].strip().replace('+', '')
                month = int(month_str) - 1
                # Calculate the date of the 15th day of the month after next
                day_of_month_after_next = datetime(year + ((today_var.month + month) // 12), ((today_var.month + month) % 12) + 1, date)
                return day_of_month_after_next.strftime("%Y-%m-%d")
            else:
                if int(lines[1].split(': ')[1]) == 0:
                    month = today_var.month
                else:
                    month = int(lines[1].split(': ')[1])
                day_of_month_after_next = datetime(year, month, date)
                return day_of_month_after_next.strftime("%Y-%m-%d")