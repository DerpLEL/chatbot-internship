from langchain.prompts import PromptTemplate
from langchain.chat_models import AzureChatOpenAI
from langchain.llms import AzureOpenAI
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.chains import LLMChain, APIChain
from langchain.chains.api.prompt import API_RESPONSE_PROMPT
from langchain.schema import Document
from langchain.tools import BaseTool
from langchain.agents import ZeroShotAgent, AgentExecutor, AgentType, initialize_agent, Tool, load_tools
from langchain.agents.agent_toolkits.openapi import planner

import requests


history_delete_general_cassify = """<|im_start|>system
given a chat history, classify whether it is in this format and answer only yes or no
EXAMPLE
INPUT:
Leave application 1:
ID: 5ab661b6-ab29-4957-a94d-44db56ba2b63
Start date: 2023-07-20T00:00:00
End date: 2023-07-21T00:00:00
Number of day(s) off: 2
OUTPUT: yes
INPUT:
Leave application 1:
ID: a066515f-2c8d-4091-8940-5f4f98eaa43b
Start date: 2023-07-20T00:00:00
End date: 2023-07-21T00:00:00
Number of day(s) off: 2

Leave application 2:
ID: a5533fb7-15ca-4a72-b25c-9dd8b8dec152
Start date: 2023-07-17T00:00:00
End date: 2023-07-18T00:00:00
Number of day(s) off: 2
Bạn muốn tôi xóa đơn nào?
OUTPUT: yes



Input: {question}

<|im_start|>assistant

Output:"""

keyword_extract_continuous = """
Given a sentence, assistant will extract the keyword as the user command, always on the botom of the input, the assistance will extracted number(int) from the user command:
EXAMPLE: 

INPUT:
Leave application 1:
ID: 5ab661b6-ab29-4957-a94d-44db56ba2b63
Start date: 2023-07-20T00:00:00
End date: 2023-07-21T00:00:00
Number of day(s) off: 2

Leave application 2:
ID: 9f2d21df-1a87-47dd-8e6c-5282e47ace5e
Start date: 2023-07-20T00:00:00
End date: 2023-07-21T00:00:00
Number of day(s) off: 2

Bạn muốn tôi xóa đơn nào? tôi muốn xóa đơn thứ 2
OUTPUT: 2

INPUT:
Leave application 1:
ID: a066515f-2c8d-4091-8940-5f4f98eaa43b
Start date: 2023-07-20T00:00:00
End date: 2023-07-21T00:00:00
Number of day(s) off: 2

Leave application 2:
ID: a5533fb7-15ca-4a72-b25c-9dd8b8dec152
Start date: 2023-07-17T00:00:00
End date: 2023-07-18T00:00:00
Number of day(s) off: 2
Bạn muốn tôi xóa đơn nào? xóa đơn 1 
OUTPUT: 2

Leave application 1
ID: b09c77dd-5eed-427e-882f-b7b70c849f49
Start date: 2023-07-17T00:00:00
End date: 2023-07-18T00:00:00
Number of day(s) off: 2
Bạn muốn tôi xóa đơn nào? xóa đơn 1 
OUTPUT: 1

EXAMPLE: 
SENTENCE: {output}
OUTPUT:"""


classifier_usecase2 = """<|im_start|>system

Given a sentence, assistant will determine if the sentence belongs in 1 of 2 categories, which are:

- LeaveApplication
- User
- Certification
- Meeting

You answer the question "Is the user's question related to ?"

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

# User_clasifier
classifier_user = """<|im_start|>system

Given a sentence, assistant will determine if the sentence belongs in 1 of 2 categories, which are:
- get user
- get manager

You answer the question "Is the user's question related to?"

EXAMPLE:
Input: thông tin cá nhân của tôi là gì
Output: get user
Input: quản lí/ sếp của tôi là ai?
Output: get manager
Input: trong năm nay, em đã nghỉ bao nhiêu ngày
Output: get user
Input: ngày sinh nhật của tôi là gì
Output: get user
Input: công việc của tôi trong công ty là gì
Output: get user

<|im_end|>
Input: {question}
<|im_start|>assistant
Output:"""


classifier_question_leave_application =""" <|im_start|>system
Given a sentence, you will putting the sentence in one of these category
- quantity general
- quanitity specific
- latest application
- latest application specific
- general


DESCRIPTION of the categories above:
- quantity general: asking about general quanity such as what is the number of my leave application
- quanitity specific: asking about quanity from the list which satisfy the follow condition
- latest application: asking question regards to the numbered application, the order of it
- general: asking question regards to show all the leave application.
EXAMPLE:
Input: số đơn xin ngày nghỉ của tôi là bao nhiêu?
Ouput: quantity general

Input: tôi hiện tại có bao nhiêu đơn ngày nghỉ?
Output: quantity general

Input: tôi có bao nhiêu đơn nghỉ phép tổng cộng?
Ouput: quantity general

Input: có bao nhiêu đơn nghỉ phép đã được chấp thuận
Output: quantity specific

Input:cho tôi thông tin của đơn xin nghỉ phép gần nhất
Ouput: latest application

Input: cho tôi biết đơn nghỉ phép gần nhất bắt đầu từ ngày bao nhiêu
Output: latest application specific

<|im_end|>




Input: {question}

<|im_start|>assistant

Output:"""

extracted_value_quantity_specific = """Given a sentence, extract a keyword value (specific string labelled below or a string or a number) , and it must be 1 value only

The value follow one of these:
  Đồng ý
  PaidLeave
If value didnt match the above, the value should be
  a number
  a string

######
EXAMPLE
SENTENCE: tổng số đơn ngày nghỉ đã được chấp thuận?
OUTPUT: Đồng ý
######
SENTENCE: tổng số đơn ngày nghỉ được trả lương?
OUTPUT: PaidLeave
######
SENTENCE: tôi hiện có bao nhiêu đơn ngày nghỉ đã được chấp thuận?
OUTPUT: Đồng ý
######
SENTENCE: đơn đã được chấp thuận??
OUTPUT: Đồng ý
######


SENTENCE: {output}
OUTPUT:"""
chat_template = """<|im_start|>system
You are an intellegent bot assistant that helps users answer their questions. Your answer must adhere to the following criteria:
- Be brief in your answers. You must use the information inside the given documentation regards to the user
- If the user greets you, respond accordingly.
- If question is in English, answer in English. If question is in Vietnamese, answer in Vietnamese
- You can only reponse to your own information question, you couldnt ask another's information.
- if value of the output is 0, The answer have to be your ____ is 0.
- if value of the output is none, null or N/A, the answer is "thông tin đó chưa cập nhật"
- if given a dictionary format, answer all of the information within that dictionary, and still if value of the output is none, null or N/A, the answer is "thông tin đó chưa cập nhật",
you have to go down to new line each information given
- if given list of dictionary format, you only show the leave application id, start date, end date and the number of day off then ask if the user want to perform any action to it
DISPLAY as the following example format

EXAMPLE:
Leave application 1:
ID: 5ab661b6-ab29-4957-a94d-44db56ba2b63
Start date: 2023-07-20T00:00:00
End date: 2023-07-21T00:00:00
Number of day(s) off: 2

Leave application 2:
ID: 9f2d21df-1a87-47dd-8e6c-5282e47ace5e
Start date: 2023-07-20T00:00:00
End date: 2023-07-21T00:00:00
Number of day(s) off: 2

Leave application 3:
ID: a066515f-2c8d-4091-8940-5f4f98eaa43b
Start date: 2023-07-20T00:00:00
End date: 2023-07-21T00:00:00
Number of day(s) off: 2

Leave application 4:
ID: a5533fb7-15ca-4a72-b25c-9dd8b8dec152
Start date: 2023-07-17T00:00:00
End date: 2023-07-18T00:00:00
Number of day(s) off: 2

Leave application 5:
ID: b09c77dd-5eed-427e-882f-b7b70c849f49
Start date: 2023-07-17T00:00:00
End date: 2023-07-18T00:00:00
Number of day(s) off: 2

- SPECIAL CASE: output of gender 0, the answer is male, if the output of gender is 1, the ouput is female

Sources:
{summaries}
<|im_end|>

Chat history:{context}

<|im_start|>user
{question}
<|im_end|>
<|im_start|>assistant

"""

delete_value_keyword = """
Given a sentence, extract a keyword value (ID formatted number or an integer) , and it must be 1 value only

EXAMPLE:
######
Input: tôi muốn xóa đơn xin nghỉ 7a9680f7-6065-45ee-97d6-094b295a2165
Output: 7a9680f7-6065-45ee-97d6-094b295a2165
######
Input: tôi muốn xóa đơn thứ nhất
Output: 1
######
Input: tôi muốn xóa đơn thứ 2
Output: 2
######
Input: tôi muốn xóa second application
Output: 2
######
Input: tôi muôn xóa đơn thứ 4th
Output: 4

SENTENCE: {output}
OUTPUT:"""
include_latest = """
Given a sentence, translate the sentence to english and check the sentence included the word "recent", "latest" or similar or not
output:
- yes
- no
EXAMPLE:
INPUT: cho tôi xóa dơn nghỉ phép
OUTPUT: no
INPUT cho tôi xóa đơn nghỉ việc gần đây nhất
OUTPUT: yes
INPUT: cho tôi xóa đơn nghỉ việc mới tạo
OUTPUT: yes
INPUT: cho tôi xóa đơn nghỉ phép đi
OUTPUT: no
SENTENCE: {output}
OUTPUT:"""
delete_leaveapp_case_classifier = """

Given a sentence, put the sentence in one of these category , and it must be 1 value only
- id
- general
- recent
DEFINITION:
- id: when sentence included application id inside it formmated like f4dfa01d-4dec-4b43-82dd-5480be195d5b
- general: when sentence only state intention wanted to delete leave application in general, or user state that they want to delete form number 1 ( example: "tôi muốn xóa đơn 1"), delete the second form or numberic 
- recent: THIS IS A SPECIAL CASE, OFTEN ASK BUT EASY MISTAKEN TO GENERAL CASE, carefully choose this category. 
when sentence only state intention wanted to delete leave recent application, recently created application. included string like "vừa tạo", "gần nhất", "gần đây nhất"
"recently", "recent", "latest"
- continnous: when input is a list of option formmated in format

EXAMPLE: 

Leave application number 1 :
Application id: f4dfa01d-4dec-4b43-82dd-5480be195d5b
From date: 2023-07-21T00:00:00
To date: 2023-07-21T00:00:00
Number day off: 0.5

Bạn muốn tôi xóa đơn nào? tôi muốn xóa đơn số 1 


EXAMPLE:
INPUT: cho tôi xóa đơn nghỉ phép abc13221312312312312
OUTPUT: id
INPUT: cho tôi xóa đơn nghỉ phép
OUTPUT: general
INPUT: cho tôi xóa đơn nghỉ phép gần nhất
OUTPUT:  recent
INPUT: tôi muốn xóa đơn xin nghỉ
OUTPUT: general
INPUT: xóa đơn xin nghỉ phép
OUTPUT: general
INPUT: cho tôi xóa đơn nghỉ phép gần nhất
OUTPUT:  recent
INPUT: cho tôi xóa đơn nghỉ phép tôi vừa tạo
OUTPUT:  recent
INPUT: tôi muốn xóa đơn nghỉ đơn số 1
OUPUT: general
INPUT: tôi muốn xóa đơn nghỉ đơn đầu tiên
OUTPUT general
INPUT: tôi muốn xóa đơn thứ 4
OUTPUT: general
SENTENCE: {output}
OUTPUT:"""

latest_application_date_classifier = """

SENTENCE: {output}
OUTPUT:"""
llm2 = AzureChatOpenAI(

            openai_api_type="azure",

            openai_api_base='https://openai-nois-intern.openai.azure.com/',

            openai_api_version="2023-03-15-preview",

            deployment_name='gpt-35-turbo-16k',

            openai_api_key='400568d9a16740b88aff437480544a39',

            temperature=0.7,

            max_tokens=600

        )

# for keyword -lateron
llm3 = AzureChatOpenAI(

            openai_api_type="azure",

            openai_api_base='https://openai-nois-intern.openai.azure.com/',

            openai_api_version="2023-03-15-preview",

            deployment_name='gpt-35-turbo-16k',

            openai_api_key='400568d9a16740b88aff437480544a39',

            temperature=0.5,

            max_tokens=600

        )

# using section

usecase2_classifier_chain = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(classifier_usecase2))

classifier_user_chain = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(classifier_user))

classifier_leave_application_get = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(classifier_question_leave_application))


value_extract = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(extracted_value_quantity_specific))

qaChain = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(chat_template))

# delete function

delete_value_keyword_get = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(delete_value_keyword))

classifier_delete_leaveapp_case = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(delete_leaveapp_case_classifier))

# keyword extract use 
include_latest_check = LLMChain(llm=llm3, prompt=PromptTemplate.from_template(include_latest)) 

# delete general keyword extract

extract_keyword_general = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(keyword_extract_continuous))

# function define
def get_users(query: str = None):
    return requests.get(url + '/api/User').json()['data']

def get_user_through_email(email):
    response = requests.get(url + f'/api/User/me?email={email}')
    if response.status_code == 200:
        return response.json()['data']

    return f'Error: {response.status_code}'


def check_manager_name(name):
    response = requests.get(url + '/api/User/manager-users').json()['data']

    for data in response:
        if data['fullName'].lower() == name.lower():
            return data['id']

    return -1
# must have url
def get_mananger_information():
  response = requests.get(url + '/api/User/manager-users').json()['data']
  return response

def get_leave_application_through_id(user_id):
  response = requests.get(url + f'/api/leaveApplication/{user_id}')
  if response.status_code == 200:
      print("pass")
      return response.json()['data']

def delete_leave_application(application_id):
  response = requests.delete(url + f'/api/leaveApplication/{application_id}')
  if response.status_code == 200:
      print("You have successfully deleted leave application " + application_id)

def new_line_formatter(response):
    # check empty
    if response == "":
        return
    # not
    else:
        final_response = ''
        paragraphs = response.split('\n\n')  # Split the response into paragraphs using '\n\n'

        for i, paragraph in enumerate(paragraphs):
            lines = paragraph.split('\n')
            paragraph_html = '<div>' + '</div><div>'.join(lines) + '</div>'
            final_response += paragraph_html
            if i < len(paragraphs) - 1:
                final_response += '<br>'  # Add an extra <div></div> between paragraphs

        return final_response
def display_leave_application(response): # input list of dictionaries response
  # displaying the application
  if response != []:
    count = 1
    text =""
    for i in response:
        text += ("Leave application number " + str(count) +" :\n")
        text += ("Application id: " +str(i["id"])  +"\n")
        text += ("From date: " + str(i["fromDate"])  + "\n")
        text +=("To date: " + str(i["toDate"]) + "\n")
        text +=("Number day off: " + str(i["numberDayOff"]) + "\n\n")
        count+=1
    
    text = new_line_formatter(text)
    print(text)
    return text
  else:
      return 
  # seperate into 3 cases: delete with form id, delete asked in general -> then tell the number, delete latest,
# after the general
email = "bui.khanh@nois.vn"
url = "https://hrm-nois-fake.azurewebsites.net/"

history_delete = ''
# start

def run_leave_application_delete(email, query, history):
    # delete
    # direct form id deletion case
# Thien: check null của số ngày nghỉ
    global history_delete
    label = classifier_delete_leaveapp_case(query)['text']
    print(label)
    if ( label == "id"):
        list100=range(1,101) #100list
        user_info = (get_user_through_email(email))
        user_id = user_info['id']
        temp_order  = extract_keyword_general(query)["text"]
        response = get_leave_application_through_id(user_id)
        print(temp_order)
        for i in list100:
            if int(temp_order) == i:
                id = response[int(int(temp_order) - 1 )]["id"]
                print("item id: " + id)
                delete_leave_application(id)
                return "Đã xóa thành công"
            

        key_value = delete_value_keyword_get(query)['text']
        print("id-pass")
        delete_leave_application(key_value)

        # create a check from list here, else return couldnt find 
        return "Đã xóa thành công"

    # implemented
    # numberic order id deletetion
    elif ( label == "general"):
        user_info = (get_user_through_email(email))
        user_id = user_info['id']
        print("general-pass")
        response = get_leave_application_through_id(user_id)
        # display the option


        if history_delete == "":
            if response == []:
                return "empty list"
            else:
                result = display_leave_application(response) # displaying all of it,
                history_delete += str(response)
                response = str(result) + "\n Bạn muốn tôi xóa đơn nào?</div>"
                return str(response)
        else:

            temp_order  = extract_keyword_general(history_delete + query)["text"]
            id = response[int(temp_order) - 1]["id"]
            print("item id: " + id)
            delete_leave_application(id)
            print("pass-general-result-empty")
            return "delete item " + str(id)

    # implemented
    # delete latest
    elif ( label == "recent"):

        user_info = (get_user_through_email(email))
        user_id = user_info['id']
        response = get_leave_application_through_id(user_id)
        label  = include_latest_check(query)['text']
        print("recent-pass")
        if label == "yes":
            if response == []:
                return "danh sách đơn xin nghỉ phép trống"
            else:
                delete_leave_application(response[0]['id'])
                return "Đã xóa thành công"
        # none check
        else:
            if history_delete == "":
                
                if response == []:
                    return "empty list"
                else:
                    result = display_leave_application(response) # displaying all of it,
                    history_delete += str(response)
                    response = str(result) + "\n Bạn muốn tôi xóa đơn nào?</div>"
                    return str(response)
            else:
                temp_order  = extract_keyword_general(history_delete + query)["text"]
                id = response[int(temp_order)]["id"]
                print("item id: " + id)
                delete_leave_application(id)
                print("pass-general-result-empty")
                return "delete item" + str(id)
