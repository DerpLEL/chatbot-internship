from langchain.prompts import PromptTemplate
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import LLMChain


from langchain.agents.agent_toolkits.openapi import planner

import requests

url = "https://hrm-nois-fake.azurewebsites.net/"


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

keyword_templ_user = """Given a sentence, extract keywords and translate English,
SPECIAL CASE: result ID must be lowercase into id.
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



classifier_user_chain = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(classifier_user))

keyword_chain = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(keyword_templ_user))

qaChain = LLMChain(llm=llm2, prompt=PromptTemplate.from_template(chat_template))


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


# existed email
def run_return_user_response(email,query ):

    get_user_type = classifier_user_chain(query)['text']
    keyword = keyword_chain(query)['text']
    user_info = (get_user_through_email(email))

    print("")
    print("user info: " + str(user_info))
    temp_result = "input: " + query + " output: " + str(user_info[keyword])
    print("temp_result: " + str(temp_result))
    print(keyword)
    result = qaChain({'summaries': temp_result,'context':"", 'question': query}, return_only_outputs=False)
    return result["text"]
