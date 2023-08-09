from langchain.prompts import PromptTemplate
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import LLMChain
from langchain.chains.api.prompt import API_RESPONSE_PROMPT

import requests


url = "https://api-hrm.nois.vn/api"
header = {}

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

# - latest application specific

# EXAMPLE 
# Input: cho tôi biết đơn nghỉ phép gần nhất bắt đầu từ ngày bao nhiêu
# Output: latest application specific

# Input: cho tôi biết note của đơn nghỉ phép gần nhất
# Output: latest application specific

# Input: cho tôi biết ngày kết thúc của đơn nghỉ phép gần nhất
# Output: latest application specific

# Input: cho tôi biết loại nghỉ phép của đơn nghỉ phép gần nhất
# Output: latest application specific
classifier_question_leave_application =""" <|im_start|>system
Given a sentence, you will putting the sentence in one of these category
- quantity general
- quanitity specific
- latest application

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
- the answer will be inside the output of the summaries, answer according to the given summaries. 
- If the user greets you, respond accordingly.
- if value of the output is none, null or N/A, the answer is "thông tin đó chưa cập nhật"
- if given a dictionary format, answer all of the information within that dictionary, and still if value of the output is none, null or N/A, the answer is "thông tin đó chưa cập nhật",
you have to go down to new line each information given
- if given list of dictionary format, you only show the leave application id, start date, end date and the number of day of
DISPLAY as the following example format

EXAMPLE:
INPUT: 'summaries': 'input: cho tôi xem số lượng đơn nghỉ phép, output: 1', 'context': '', 'question': 'cho tôi xem số lượng đơn nghỉ phép'
OUTPUT: số lượng đơn nghỉ phép bạn đang hiện đã nộp là 1

INPUT: 'summaries': 'input: cho tôi xem số lượng đơn nghỉ phép, output: 3', 'context': '', 'question': 'cho tôi xem số lượng đơn nghỉ phép'
OUTPUT: số lượng đơn nghỉ phép bạn đang hiện đã nộp là 3

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


# function define
def get_leave_application():
    """
    Input: None

    Output:
        temp_list: list of dictionary to displaying all the leave appliciation 
    Purpose: get leave application from HRM from website url 
    """    
    response = requests.get(url + "/leaveapplication/paging?pageIndex=0&pageSize=50&type=0", headers=header)
    temp_list = []
    if response.status_code == 200:
        for i in response.json()['data']['items']:
            if i["reviewStatusName"] != "Đồng ý":
                temp_list.append(i) 
        return temp_list
    else:
        return
  

def new_line_formatter(response):
    """
    Input: response (str)

    Output:
        temp_list: formatted output (str)
    Purpose: make the input str go under new line
    """        
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
    
def display_leave_application(response):
    """
    Input: None

    Output:
        temp_list: list of dictionary to displaying all the leave appliciation 
    Purpose: get leave application from HRM from website url 
    """  
   # input list of dictionaries response
  # displaying the application
    print("response - general - pass: " + str(response))
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
# single dict
def display_single_leave_application(response): 
    """
    Input: email: email to search the current user to sql server
            

    Output: history of history_delete
    Purpose: get history_delete from sql server 
    """   
    # input list of dictionaries response
    # displaying the application
    print("response - general - pass: " + str(response))
    if response != []:
        count = 1
        text =""
        text += ("Leave application number " + str(count) +" :\n")
        text += ("Application id: " +str(response["id"])  +"\n")
        text += ("From date: " + str(response["fromDate"])  + "\n")
        text +=("To date: " + str(response["toDate"]) + "\n")
        text +=("Number day off: " + str(response["numberDayOff"]) + "\n\n")
        count+=1
        text = new_line_formatter(text)
        print(text)
        return text
    else:
        return 


# history_delete = ""
def run_get_leave_application(email, query, token):
    """
    Input: email: email to search the current user to sql server
            query: question/command from user 
            token: HRM token that the user inputted
    Output: None
    Purpose: function to run all function of get_leave_application (run this in the chatbot.py)
    """        
    global header
    global history_delete
    header = {"Authorization": f"Bearer {token}"}
    label_get_application = classifier_leave_application_get(query)['text']
    # THIS IS FOR general --> ask again if user want to perform any action with it, save these into history
    
    print(label_get_application)
    response = get_leave_application()
    if response != []:
        if (label_get_application =="general"):
            result = display_leave_application(response) + "\n Bạn muốn tôi giúp gì thêm "
            # history_delete += result
            return result

        # THIS IS FOR quantity general
        elif (label_get_application =="quantity general"):
            size_of_leave_application = len(response)
            temp_result = "input: " + query + ", output: " + str(size_of_leave_application)
            print(temp_result)
            result = qaChain({'summaries': temp_result,'context':"", 'question': query}, return_only_outputs=False)
            print(result)
            return result["text"]


        # THIS IS FOR quantity specific
        # done tổng số đơn ngày nghỉ đã được chấp thuận
        # done tổng số đơn ngày nghỉ được trả lương
        # done tổng số đơn ngày nghỉ được có note là 2nd
        # need to add more value since dont know the exact discrete val
        elif (label_get_application =="quantity specific"):
            counter = 0
            keyword = keyword_chain(query)['text']
            value_to_compare = value_extract(query)['text']
            print(keyword)
            print(value_to_compare)
            # list of dict for leav3 application
            size_of_leave_application = len(response)
            num = 0
            for i in response:
                if (i[keyword] == value_to_compare):
                    counter+= 1
                    num += 1
            temp_result = " output: " + str(counter) # "input: " + query + 
            result = qaChain({'summaries': temp_result,'context':"", 'question': query}, return_only_outputs=False)
            return result["text"]
        # THIS IS FOR latest application
        elif (label_get_application == "latest application"):
            response = display_single_leave_application(response[0])
            return response + "bạn muốn tôi làm gì tiếp"


        # THIS IS FOR latest application specific
        # elif (label_get_application == "latest application specific"):     
        #     keyword = keyword_chain(query)['text']
        #     print("first response: " + str(response[0]))
        #     display_response = display_single_leave_application(response[0])
        #     try:
        #         temp_result = "input: " + query + " output: " + str(response[0][keyword])
        #     except:
        #         return display_response
        #     result = qaChain({'summaries': temp_result,'context':"", 'question': query}, return_only_outputs=False)
        #     return result["text"]

    else:
        return "currently you have no leave application waiting"