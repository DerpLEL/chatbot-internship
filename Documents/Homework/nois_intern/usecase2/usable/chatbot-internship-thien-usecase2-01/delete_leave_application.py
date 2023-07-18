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
from langchain.requests import TextRequestsWrapper
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains.api import open_meteo_docs
from datetime import datetime, timedelta
import requests
import pandas as pd
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from langchain.chains.qa_with_sources import load_qa_with_sources_chain


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

Given a sentence, assistant will determine if the sentence belongs in 1 of 3 categories, which are:
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
keyword_templ_leave_application = """Given a sentence, extract keywords and translate English, and it must be 1 keyword only

SPECIAL CASE:
if the input include "đơn" + "chấp thuận", do not return totalRecord, output should return "reviewStatusName"
if the input include "đơn nghỉ " + "chấp thuận" or "đồng ý", do not return totalRecord, output should return "reviewStatusName"

The keyword MUST follow one of these:

      "id": ,
      "registerDate": ,
      "fromDate": ,
      "toDate": ,
      "numberDayOff": ,
      "leaveApplicationNote": ,
      "reviewStatus": ,
      "reviewNote": ,
      "leaveApplicationType": ,
      "userId": ,
      "jobTitle": ,
      "userName": ,
      "reviewUserId": ,
      "reviewUser": ,
      "reviewStatusName": ,
      "reviewDate": ,
      "periodType": ,
      "periodTypeName": ,
      "relatedUserId": ,
      "relatedUser": ,
      "totalRecord":

######
EXAMPLE
SENTENCE: id của tôi là gì?
OUTPUT: id
######
SENTENCE: đơn ghi nghỉ từ ngày nào?
OUTPUT: fromDate
######
SENTENCE: đơn ghi nghỉ tới ngày nào?
OUTPUT: toDate
######
SENTENCE: tổng thời gian nghỉ là nhiêu ngày?
OUTPUT: numberDayOff
######
SENTENCE: đơn đã được chấp thuận?
OUTPUT: reviewStatusName

#####
SENTENCE: tổng số đơn ngày nghỉ được trả lương?
OUTPUT: leaveApplicationType
######
SENTENCE: đơn xin nghỉ của tôi có được trả lương không?
OUTPUT: leaveApplicationType
######
SENTENCE: note của đơn nghỉ của tôi là gì?
OUTPUT: leaveApplicationNote
######
SPECIAL CASE:
Input: tôi hiện có bao nhiêu đơn ngày nghỉ đã được chấp thuận?
Output: reviewStatusName
######
Input: ngày nghỉ đã được chấp thuận?
Output: reviewStatusName
#####
Input: đơn đã được chấp thuận?
Output: reviewStatusName
#####
Input: tổng đơn nghỉ được đồng ý
Output: reviewStatusName






SENTENCE: {output}
OUTPUT:"""

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

delete_leaveapp_case_classifier = """
Given a sentence, put the sentence in one of these category , and it must be 1 value only
- delete by id
- delete general
- delete latest

DEFINITION:
delete by id: when sentence included application id inside it
delete general: when sentence only state intention wanted to delete leave application
delete latest: when senetence stated that the user want to delete the latest leave application

EXAMPLE:
INPUT: cho tôi xóa đơn nghỉ phép abc13221312312312312
OUTPUT: delete by id
INPUT: cho tôi xóa đơn nghỉ phép
OUTPUT: delete general
INPUT: cho tôi xóa đơn nghỉ phép gần nhất
OUTPUT: delete latest

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

keyword_chain = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(keyword_templ_leave_application))

value_extract = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(extracted_value_quantity_specific))

qaChain = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(chat_template))

# delete function

delete_value_keyword_get = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(delete_value_keyword))

classifier_delete_leaveapp_case = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(delete_leaveapp_case_classifier))


# function define
def get_users(query: str = None):
    return requests.get(url + '/api/User').json()['data']

def get_user_through_email(email):
    response = requests.get(url + f'/api/User/me?email={email}')
    if response.status_code == 200:
        return response.json()['data']

    return f'Error: {response.status_code}'

def get_user_by_id(ID: str):
    reply = requests.get(url + f'/api/User/me?id={ID}')
    if response.status_code != 200:
        return f'Error: {response.status_code}'

    if not reply.json()['data']:
        return "Wrong ID, recheck your input."

    return reply.json()['data']

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

def display_leave_application(response): # input list of dictionaries response
  # displaying the application
  count = 1
  text =""
  for i in response:
      text += ("Leave application number " + count +" :\n")
      text += ("application id: " +i["id" +"\n"])
      text += ("From date: " + i["fromDate" + "\n"])
      text +=("To date: " + i["toDate"] + "\n")
      text +=("Number day off: " + i["numberDayOff"] + "\n\n")
      return text
  
  # seperate into 3 cases: delete with form id, delete asked in general -> then tell the number, delete latest,
# after the general
email = "bui.khanh@nois.vn"
url = "https://hrm-nois-fake.azurewebsites.net/"


# start

def run_leave_application_delete(email, query):

    # replicate second command for genereal to delete 

    # def next_command(response,history ):
    # query = "cho tôi xóa đơn thứ 1"
    # print("next query: " + query)
    # keyword = delete_value_keyword_get(query)
    # keyword = int(keyword['text'])
    # keyword -= 1

    # delete_id = response[keyword]["id"]
    # # didnt add exception ( out of index)
    # print("delete id: " + delete_id)
    # delete_leave_application(delete_id)

    # response = get_leave_application_through_id(user_id)
    # # display the option



    # delete
    # direct form id deletion case
# Thien: check null của số ngày nghỉ
    history = ""
    query = "tôi muốn xóa đơn xin nghỉ gần nhất"
    label = classifier_delete_leaveapp_case(query)['text']
    print(label)
    if ( label == "delete by id"):
        key_value = delete_value_keyword_get(query)['text']
        print(key_value)
        delete_leave_application(key_value)
        return "Đã xóa thành công"

    # implemented
    # numberic order id deletetion
    elif ( label == "delete general"):
        user_info = (get_user_through_email(email))
        user_id = user_info['id']
        print("user_id: " + user_id)
        response = get_leave_application_through_id(user_id)
        # display the option
        result = display_leave_application(response) # displaying all of it,
        history += str(result)

        print(result + "Bạn muốn tôi giúp gì tiếp?")
        # later on after displaying the option
        # key_value = delete_value_keyword_get(query)['text']
        # next_command(response,history)
        return "Đã xóa thành công"



    # implemented
    # delete latest
    elif ( label == "delete latest"):
        user_info = (get_user_through_email(email))
        user_id = user_info['id']
        print("user_id: " + user_id)
        response = get_leave_application_through_id(user_id)
        print(response)
        delete_leave_application(response[0]['id'])
        return "Đã xóa thành công"