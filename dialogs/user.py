from langchain.prompts import PromptTemplate
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import LLMChain


from langchain.agents.agent_toolkits.openapi import planner

import requests

url = "https://api-hrm.nois.vn/api/user/me"
header = {}

# User_clasifier
classifier_user = """<|im_start|>system

Given a sentence, assistant will determine if the sentence belongs in 1 of 2 categories, which are:
- get user
- get user speciffic

You answer the question "Is the user's question related to?"

EXAMPLE:
Input: thông tin cá nhân của tôi là gì
Output: get user specific

Input: trong năm nay, em đã nghỉ bao nhiêu ngày
Output: get user specific
Input: ngày sinh nhật của tôi là gì
Output: get user specific
Input: công việc của tôi trong công ty là gì
Output: get user specific

INPUT: cho tôi thông tin của tôi
OUTPUT: get user 
INPUT: thông tin của tôi là gì
OUTPUT: get user
INPUT: cho tôi biết tổng thông tin của tôi?
OUTPUT: get user
<|im_end|>
Input: {question}
<|im_start|>assistant
Output:"""


keyword_templ_user = """Given a sentence, extract keywords and translate English,
SPECIAL CASE: result ID must be lowercase into id.
If there are 2 or more keyword, put them in this format id-email-name-fullname
The keyword MUST follow one of these:
'id': ,
 'name': ,
 'email': ,
 'fullName': ,
 'jobTitle': ,
 'mobilePhone': ,
 'birthday': ,
 'offDay': ,
 'yearOffDay': ,
 'maxDayOff': ,
 'remainDayOffLastYear': ,
 'offDayUseRamainDayOffLastYear': ,
 'gender': ,
 'personalEmail': ,
 'avatar': ,
 'acceptOfferDate': ,
 'quitJobDate': ,
 'bonusDayOff': ,
 'managerId': ,
 'managerFullName': ,
 'departmentId': ,
 'departmentName': '',
 'groupUserId': ,
 'groupUserName': ,
 'hasLeft': ,
 'identityCard': ,
 'dateOfIssue': ,
 'issuedBy': ,
 'placeOfTemporaryResidence': ,
 'placeOfResidence': ,
 'relativeName': ,
 'relationship': ,
 'relativeMobilePhone': ,
 'hasBankAccount': ,
 'bankName': ,
 'bankBranch': ,
 'bankAccountNumber': ,
 'birthPlace': ,
 'isFirstLogin': ,
 'roles': ,
 'taxIdentificationNumber': ,
 'education': ,
 'jobId': ,
 'jobName': ,
 'levelId': ,
 'levelName':

######
EXAMPLE
SENTENCE: id của tôi là gì?
OUTPUT: id
######
SENTENCE: ngày sinh nhật của tôi là gì?
OUTPUT: birthday
######
SENTENCE: vai trò trong công ty của tôi là gì?
OUTPUT: roles
######
SENTENCE: tên ngân hàng của tôi là gì?
OUTPUT: bankName

SENTENCE: tên của tôi và email của tôi
OUTPUT: name-email

SENTENCE: họ tên đầy đủ của tôi và email của tôi
OUTPUT: fullname-email 

SENTENCE: {output}
OUTPUT:"""


chat_template = """<|im_start|>system
You are an intellegent bot assistant that helps users answer their questions. Your answer must adhere to the following criteria:
- You must use the information inside the given documentation regards to the user
- If the user greets you, respond accordingly.
- If question is in English, answer in English. If question is in Vietnamese, answer in Vietnamese
- You can only reponse to your own information question, you couldnt ask another's information.
- if value of the output is 0, The answer have to be your ____ is 0.
- if value of the output is none, null or N/A, the answer is "thông tin đó chưa cập nhật"
- there will be cases that the output will be more than 2 value inside, it will be answered from left to right of the question query
- SPECIAL CASE: output of gender 0, the answer is male, if the output of gender is 1, the output is female


Sources:
{summaries}
<|im_end|>

Chat history:{context}

<|im_start|>user
{question}
<|im_end|>
<|im_start|>assistant

"""


llm2 = AzureChatOpenAI(

            openai_api_type="azure",

            openai_api_base='https://openai-nois-intern.openai.azure.com/',

            openai_api_version="2023-03-15-preview",

            deployment_name='gpt-35-turbo-16k',

            openai_api_key='400568d9a16740b88aff437480544a39',

            temperature=0.7,

            max_tokens=600

        )

# for keyword -later on
llm3 = AzureChatOpenAI(

            openai_api_type="azure",

            openai_api_base='https://openai-nois-intern.openai.azure.com/',

            openai_api_version="2023-03-15-preview",

            deployment_name='gpt-35-turbo-16k',

            openai_api_key='400568d9a16740b88aff437480544a39',

            temperature=0.5,

            max_tokens=600

        )



classifier_user_chain = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(classifier_user))

keyword_chain = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(keyword_templ_user))

qaChain = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(chat_template))


# function define
def get_user():
  response = requests.get(url, headers=header)  
  return response.json()['data'] 


def display_single_leave_application(response): # input list of dictionaries response
  # displaying the application
#   print("response - general - pass: " + str(response))
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
    # print(text)
    return text
  else:
      return 

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
def display_user_information(response): # input list of dictionaries response
  # displaying the application
#   print("response - general - pass: " + str(response)) # error here means token expired
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
    # print(text)
    return text
  else:
      return 
# must have url


def convertList(string):
    li = list(string.split("-"))
    return li


def run_return_user_response(email,query , token):
    global header
    header = {"Authorization": f"Bearer {token}"}
    case_classifier = classifier_user_chain(query)
    # print("get classifer: " + str(case_classifier))
    if case_classifier['text'] == "get user":
        response = display_single_leave_application()
        return response
    elif case_classifier['text'] =="get user specific":
        user_info = get_user()
        keyword = keyword_chain(query)['text']
        keyword_list = convertList(keyword)
        temp_answer = ""
        if len(keyword_list) > 1:
            for i in keyword_list:
                temp_answer += str(user_info[i])
            temp_result = "input: " + query + " output: " + str(temp_answer)
        else:
           temp_result = "input: " + query + " output: " + str(user_info[keyword])
        # # print("user info: " + str(user_info))
        # print("temp_result: " + str(temp_result))
        # print(keyword)
        result = qaChain({'summaries': temp_result,'context':"", 'question': query}, return_only_outputs=False)
        return result["text"]
    else:
       return "error"
