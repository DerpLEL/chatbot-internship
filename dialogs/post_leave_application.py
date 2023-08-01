from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.chains import LLMChain
from langchain.chat_models import AzureChatOpenAI
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from datetime import datetime, timedelta

import requests
import numpy as np

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


keyword_leave_application = """<|im_start|>system
Given a sentence and a conversation, assistant will extract keywords based on the conversation and the sentence.
Your output will be on one line, separated by commas. Do not duplicate keywords.
Assume the context is about the companies unless specified otherwise. Only return the keywords, do not output anything else.
Output MUST JUST have 2 data fields: 'time', 'cause'. If any field is missing, the value of that data field is ''

EXAMPLE
Input: buổi sáng
Output: 'sáng',''
Input: buổi chiều
Output: 'chiều',''
Input: nguyên ngày
Output: 'cả nyày',''
Input: với lí do đi công tác
Output: '','đi công tác'
Input: nhà có việc gấp
Output: '','nhà có việc gấp'
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

confirm_template = """<|im_start|>system
Given a sentence, assistant will determine if the sentence belongs in 1 of 2 categories, which are:
- "yes"
- "no"
- "neutral"
You answer the question "Does user input mean consent?"
"yes": user agree (for example: yes, ok, ờ, có, ừ, um, uhm, okie, ô kê, đồng ý...)
"no": user not agree (for example: không, không đồng ý,...)
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



chain_leave_application = LLMChain(llm=llm3, prompt=PromptTemplate.from_template(keyword_leave_application))
date_determine_chain = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(date_determine))
chain_bANDe= LLMChain(llm=llm3, prompt=PromptTemplate.from_template(keyword_bANDe))
specific_date_chain = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(check_specific_date))
chain_specific_weekday = LLMChain(llm=llm3, prompt=PromptTemplate.from_template(keyword_specific_weekday))
chain_specific_date = LLMChain(llm=llm3, prompt=PromptTemplate.from_template(keyword_specific_date))
qa_chain = load_qa_with_sources_chain(llm=llm, chain_type="stuff", prompt=PromptTemplate.from_template(chat_template))
chain_session = LLMChain(llm=llm3, prompt=PromptTemplate.from_template(keyword_session))
confirm_chain = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(confirm_template))

today_var = datetime.now().date()
leave_application_form = {
            'start_date': '',
            'end_date': '',
            'duration': 0,
            'note': '',
            'periodType': -1,
        }
confirm_delete = False


def post_leave_application_func(user, query, token):
    try:
        global leave_application_form
        global confirm_delete
        response_data = requests.models.Response()
        response_data.status_code = 0

        keywords = chain_leave_application({'question': query, 'context':''})['text']
        print(keywords)
        values_keywords = keywords.split(",")
        time = values_keywords[0].strip("'")
        note = values_keywords[1].strip("'")
        if not leave_application_form['note']:
            leave_application_form['note'] = note
        print(time)
        print(date_determine_chain(time)['text'])

        if "es" in date_determine_chain(time)['text']:
            keywords_bANDe = chain_bANDe({'question': query, 'context':''})['text']
            # response = keywords_bANDe
            values_keywords_bANDe = keywords_bANDe.split(",")
            begin_date = values_keywords_bANDe[0].strip("'")
            end_date = values_keywords_bANDe[1].strip("'")
            if not leave_application_form['start_date']:
                leave_application_form['start_date'] = date_processing(begin_date)
            if not leave_application_form['end_date']:
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
            print(split_string_session_keywords)
            print(date_off)
            if not leave_application_form['start_date']:
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

            # response = str(leave_application_form)

        print(leave_application_form['start_date'], '%Y-%m-%d')
        leave_application_form_string = ''
        if datetime.strptime(leave_application_form['start_date'], '%Y-%m-%d').weekday() == 5 or datetime.strptime(leave_application_form['start_date'], '%Y-%m-%d').weekday() == 6:
            leave_application_form['start_date'] = ''
            leave_application_form_string += 'Hiện tại ngày bạn muốn submit nghỉ' + leave_application_form['start_date'] + 'là ngày cuối tuần. Bạn có thể kiểm tra lại ngày bạn muốn submit được không? Vì ngày bạn muốn nghỉ là ngày cuối tuần.'
        if datetime.strptime(leave_application_form['end_date'], '%Y-%m-%d').weekday() == 5 or datetime.strptime(leave_application_form['end_date'], '%Y-%m-%d').weekday() == 6:
            leave_application_form['end_date'] = ''
            leave_application_form_string += 'Hiện tại ngày bạn muốn submit nghỉ' + leave_application_form['end_date'] + 'là ngày cuối tuần. Bạn có thể kiểm tra lại ngày bạn muốn submit được không? Vì ngày bạn muốn nghỉ là ngày cuối tuần.'
        if leave_application_form['start_date'] and leave_application_form['end_date']:
            if leave_application_form['start_date'] == '':
                leave_application_form_string += 'Chưa cung cấp ngày bắt đầu nghỉ.'
            if leave_application_form['end_date'] == '':
                leave_application_form_string += 'Chưa cung cấp ngày kết thúc nghỉ.'
            if leave_application_form['note'] == '':
                leave_application_form_string += 'Chưa cung cấp nguyên nhân nghỉ.'
            if leave_application_form['periodType'] == -1:
                leave_application_form_string += 'Chưa cung cấp buổi nghỉ(sáng, chiều hay cả ngày).'
        
        if leave_application_form_string == '':
            if leave_application_form['periodType'] == 0:
                periodType = "Cả ngày"
            elif leave_application_form['periodType'] == 1:
                periodType = "Buổi sáng"
            elif leave_application_form['periodType'] == 2:
                periodType = "Buổi chiều"
            reviewUser = "LÝ MINH QUÂN"

            response = f"""Form submit ngày nghỉ của bạn:\n
            ______________________________________________________________________
            Ngày gửi đơn: {today_var}
            Người duyệt: {reviewUser}
            Ngày bắt đầu nghỉ: {leave_application_form['start_date']}
            Ngày kết thúc nghỉ: {leave_application_form['end_date']}
            Nghỉ buổi: {periodType}
            Tổng thời gian nghỉ: {leave_application_form['duration']}
            Lí do: {leave_application_form['note']}
            ______________________________________________________________________\n
            Bạn có muốn submit đơn nghỉ phép này không?"""
            print(confirm_chain(query)['text'])
            confirm = confirm_chain(query)['text']

            if 'es' in confirm and not confirm_delete:
                url = "https://api-hrm.nois.vn/api/leaveapplication"
                data = {
                    "reviewUserId": 139,
                    "relatedUserId": "",
                    "fromDate": datetime.strptime(leave_application_form['start_date'], '%Y-%m-%d').strftime('%m/%d/%Y'),
                    "toDate": datetime.strptime(leave_application_form['end_date'], '%Y-%m-%d').strftime('%m/%d/%Y'),
                    "leaveApplicationTypeId": 2,
                    "leaveApplicationNote": leave_application_form['note'],
                    "numberOffDay": leave_application_form['duration']
                }

                headers = {
                    "Authorization": f"Bearer {token}"
                }

                # Make the request
                response_data = requests.post(url, json=data, headers=headers)

                print(response_data.status_code)

        #         response_data = requests.post('https://hrm-nois-fake.azurewebsites.net/api/LeaveApplication/Submit', json = {
        #     "userId": 'c4edb6f7-56c8-444a-803d-5a6c77707e60',
        #     "reviewUserId": '139',
        #     "relatedUserId": "string",
        #     "fromDate": leave_application_form['start_date'],
        #     "toDate":leave_application_form['end_date'],
        #     "leaveApplicationTypeId": 1,
        #     "leaveApplicationNote": leave_application_form['note'],
        #     "periodType": leave_application_form['periodType'],
        #     "numberOffDay": leave_application_form['duration'],
        # })
        #         print(response_data.text)

                leave_application_form = {
                'start_date': '',
                'end_date': '',
                'duration': 0,
                'note': '',
                'periodType': -1,
            }
                response = f"""Đã cung cấp đủ thông tin. Đơn sẽ sớm được duyệt. Cảm ơn bạn đã gửi form.
                Bạn có cần tôi giúp đỡ gì thêm không ạ?"""

            elif 'es' in confirm and confirm_delete:
                leave_application_form = {
                'start_date': '',
                'end_date': '',
                'duration': 0,
                'note': '',
                'periodType': -1,
            }
                response_data.status_code = 100
                response = f"""Đơn nghỉ phép của bạn đã xóa. Bạn có thể gửi một Đơn nghỉ phép khác"""
                confirm_delete = False
                
            elif 'no'in confirm:
                response = f"""Bạn không muốn giữ Đơn nghỉ phép này nữa hả?"""
                confirm_delete = True
            else:
                pass
        else:
            result_doc = "Input: " + "Quản lý, còn thiếu thông tin gì về Đơn nghỉ phép nữa không." +"\n Output: " + leave_application_form_string
            doc = [Document(page_content= result_doc,
                                    metadata={'@search.score': 0,
                                            'metadata_storage_name': 'local-source', 'source': f'doc-0'})]

            response = qa_chain({'input_documents': doc, 'question': query, 'context': '',
                                    'user_info': f'''The user chatting with you is named {user['username']}, with email: {user['mail']}. 
                                    '''},
                                return_only_outputs=False)['output_text']
        return [response,response_data]
    except Exception as e:
        return str(e) + 'Có phải bạn đang muốn submit ngày nghỉ đúng không? Hiện tại tôi thấy hình như bạn thiếu thời gian nghỉ.'
    

def date_processing(date_off):
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