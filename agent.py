from langchain.prompts import PromptTemplate
from langchain.chat_models import AzureChatOpenAI
from langchain.llms import AzureOpenAI
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.chains import LLMChain, APIChain
from langchain.chains.api.prompt import API_RESPONSE_PROMPT
from langchain.schema import Document
from langchain.tools import BaseTool
from langchain.agents import ZeroShotAgent, AgentExecutor, AgentType, initialize_agent, Tool, load_tools
from langchain.schema import AgentFinish
from langchain.agents.agent_toolkits.openapi import planner
from langchain.requests import TextRequestsWrapper
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains.api import open_meteo_docs
import datetime
import requests
import pandas as pd
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
import numpy as np
from langchain.callbacks.base import BaseCallbackHandler
from typing import Any, Dict, List
import requests


llm3 = AzureChatOpenAI(
    openai_api_type="azure",
    openai_api_base='https://openai-nois-intern.openai.azure.com/',
    openai_api_version="2023-03-15-preview",
    deployment_name='gpt-35-turbo-16k',
    openai_api_key='400568d9a16740b88aff437480544a39',
    temperature=0.0,
    max_tokens=600
)

url = "https://hrm-nois-fake.azurewebsites.net/"
email = 'bao.ho@nois.vn'
dtime = datetime.datetime
date = dtime.now().strftime("%Y-%m-%d")


def get_users(query: str = None):
    return requests.get(url + '/api/User').json()['data']


def delAll(ID: str):
    lst = []
    get_reply = requests.get(url + f"/api/LeaveApplication/{ID}").json()
    for i in get_reply['data']:
        lst.append(i['id'])

    for i in lst:
        del_reply = requests.delete(url + f"/api/LeaveApplication/{i}")
        print(del_reply.text)


def get_user_by_email(query: str = None):
    user_email = email
    if '@' in query and query != user_email:
        return f"Access denied, only the data of the current user {user_email} can be accessed."

    response = requests.get(url + f'/api/User/me?email={user_email}')

    if response.status_code == 200:
        return_text = "User info:\n"
        user_data = response.json()['data']

        for i in user_data.items():
            return_text += f"- {i[0]}: {i[1]}\n"
            if i[0] == "maxDayOff":
                return_text += f"- remainingOffDays: {user_data['maxDayOff'] - user_data['offDay']}\n"

        return return_text

    return f'Error: {response.status_code}'


def output_to_user(query: str = None):
    #     print(query)
    return f'Message "{query}" sent to user.'


def get_userName(query: str = None):
    user_email = email
    response = requests.get(url + f'/api/User/me?email={user_email}')
    if response.status_code == 200:
        return response.json()['data']['name']

    return f'Error: {response.status_code}'


def get_userId(query: str = None):
    user_email = email
    response = requests.get(url + f'/api/User/me?email={user_email}')
    if response.status_code == 200:
        return response.json()['data']['id']

    return f'Error: {response.status_code}'


def get_leave_applications(query: str = None):
    userId = get_userId(email)

    applis = requests.get(url + f'/api/LeaveApplication/{userId}').json()['data']

    #     applis = [i for i in applis if i['reviewStatusName'] != "Đồng ý"]

    string = ""
    counter = 1
    for i in applis:
        string += f"Leave application {counter}:\n"
        string += f"ID: {i['id']}\n"
        string += f"Start date: {i['fromDate']}\n"
        string += f"End date: {i['toDate']}\n"
        string += f"Number of day(s) off: {i['numberDayOff']}\n\n"

        counter += 1

    return string


def delete_leave_applications(target: str = "Default"):
    applis = requests.get(url + f'/api/LeaveApplication/{get_userId(email)}').json()['data']

    appli = [i for i in applis if i['id'] == target]

    string = ""
    for i in appli:
        string += f"ID: {i['id']}\n"
        string += f"Start date: {i['fromDate']}\n"
        string += f"End date: {i['toDate']}\n"
        string += f"Number of day(s) off: {i['numberDayOff']}\n\n"

    user_confirm = input(string + "Are you sure you wnat to delete this application? Type 1 for yes, 0 for no.\n")

    while user_confirm != '1' and user_confirm != '0':
        user_confirm = input("Invalid input. Type 1 for yes, 0 for no.\n")

    if user_confirm == '0':
        return "User cancelled the leave application deletion process."

    return requests.delete(url + f'/api/LeaveApplication/{target}').json()['message']


def check_manager_name(name):
    response = requests.get(url + '/api/User/manager-users').json()['data']

    for data in response:
        if data['fullName'].lower() == name.lower():
            return data['id']

    return -1


def check_manager_id(managerId):
    response = requests.get(url + '/api/User/manager-users').json()['data']

    for data in response:
        if data['id'] == int(managerId):
            return True

    return False


def post_method(user_id, manager_id, start_date, end_date):
    start_dtime = dtime.strptime(start_date, "%Y-%m-%d")
    end_dtime = dtime.strptime(end_date, '%Y-%m-%d')

    num_days = 0

    if end_dtime == start_dtime:
        reply = input(
            "Do you want to take the whole day off or only half day off? Type 1 for whole day off, and 0 for half day off.\n")

        while reply != "1" and reply != "0":
            reply = input("Invalid input. Type 1 for whole day off, and 0 for half day off.\n")

        num_days = 0.5

        if reply == "1":
            num_days = 1

    else:
        num_days = int(np.busday_count(start_date, end_date)) + 1

    string = f'''Leave application details:
    - UserId: {user_id}
    - ManagerId: {manager_id}
    - Start date: {start_date}
    - End date: {end_date}
    - Number of day(s) off: {num_days}
Is this information correct? Type 1 to submit, type 0 if you want to tell the bot to edit the form.\n'''

    user_confirm = input(string)

    while user_confirm != "1" and user_confirm != "0":
        user_confirm = input("Invalid input. Type 1 to submit, type 0 if you want to tell the bot to edit the form.\n")

    if user_confirm.strip() != "1":
        user_edit = input("Tell the bot what you want to edit in the form here:\n")

        return user_edit

    response = requests.post('https://hrm-nois-fake.azurewebsites.net/api/LeaveApplication/Submit', json={
        "userId": user_id,
        "reviewUserId": manager_id,
        "relatedUserId": "string",
        "fromDate": start_date,
        "toDate": end_date,
        "leaveApplicationTypeId": 0,
        "leaveApplicationNote": "string",
        "periodType": 0,
        "numberOffDay": num_days
    })

    return response.json()['message']


lst = []


def submitLeaveApplication(args: str):
    global lst
    lst = args.split(', ')

    if len(lst) != 4:
        return "Incorrect number of arguments, this function requires 4 arguments: user's id, manager's id, start date and end date."

    if '-' not in lst[0]:
        return "Incorrect ID. You can find the correct ID by using the HRM get by email tool."

    if check_manager_name(lst[1]) == -1 and check_manager_id(lst[1]) == False:
        return "Ask the user for the correct manager's name. The user either didn't give you a name or gave you the wrong name."

    if '-' not in lst[2]:
        return "Ask the user when they want to start their leave. Infer the date based on the user's answer."

    if dtime.strptime(lst[2], "%Y-%m-%d") < dtime.strptime(date, "%Y-%m-%d"):
        return "Start date cannot be earlier than current date, ask the user for another date."

    if dtime.strptime(lst[2], "%Y-%m-%d").weekday() in [5, 6]:
        return "Start date cannot be on the weekend, ask the user for another date."

    if '-' not in lst[3]:
        return "Ask the user when they want to end their leave. Infer the date based on the user's answer."

    if dtime.strptime(lst[3], "%Y-%m-%d") < dtime.strptime(lst[2], "%Y-%m-%d"):
        return "End date cannot be earlier than start date, ask the user for another date."

    if dtime.strptime(lst[3], "%Y-%m-%d").weekday() in [5, 6]:
        return "End date cannot be on the weekend, ask the user for another date."

    print("\nUserId: ", lst[0])
    print("ReviewerId: ", lst[1])
    print("Start date: ", lst[2])
    print("End date: ", lst[3])

    reply = post_method(lst[0], int(lst[1]), lst[2], lst[3])

    return reply


tool1 = [
    Tool(
        name='HRM get user data',
        func=get_user_by_email,
        description='useful for getting data of the current user, data include fullName, birthday, bankAccountNumber, etc. This tool does not take any inputs.'
    ),

    #     Tool(
    #         name='Output to user',
    #         func=output_to_user,
    #         description='useful for sending messages to the user as they cannot see your thought, actions, etc. This tool takes in your message and sends it to the user.'
    #     ),

    #     Tool(
    #         name='End conversation',
    #         func=end_convo,
    #         description='useful for ending the conversation if the user cancels the task or you cannot complete the task.'
    #     ),

    #     Tool(
    #         name='Do nothing',
    #         func=nothing,
    #         description='useful for filling in Action: after Thought: if the task can\'t be done or the task is cancelled.'
    #     ),
]

human = load_tools(['human'])
tool1.extend(human)

prefix1 = f"""You are an intelligent assistant helping user find his/her information in HRM system by using tool. 
The user chatting with you is {get_userName(email)} with the email {email}. If question/data are not about them, tell them you don't have access.
DO NOT use data of the user {email} to answer questions about other users.
You have access to the following tools:"""

temp1_backup = f'''

Examples: 
Question: What is my date of birth?
Thought: The user chatting with me has the email {email}.
Thought: find the data of user by user's email.
Action: HRM get user data
Action Input: {email}
Observation: ...
Thought: I now know the final answer
Final Answer: Your date of birth is ...

Question: What is hung.bui@nois.vn's bank account number?
Thought: The user chatting with me has the email {email}.
Thought: the question is not about the current user, so I can't answer the question.
Action: human
Action Input: I'm sorry but I don't have access to that information, can I help you with anything else?
Observation: No
Thought: I now know the final answer
Final Answer: 

'''

temp1 = f'''

Examples: 
Question: What is my date of birth?
Thought: The user chatting with me has the email {email}.
Thought: find the data of user by user's email.
Action: HRM get user data
Action Input: {email}
Observation: ...
Thought: I now know the final answer
Final Answer: Your date of birth is ...

Question: What is hung.bui@nois.vn's bank account number?
Thought: The user chatting with me is {get_userName(email)} with the email {email}.
Thought: the question is not about the current user, so I can't answer the question.
Final Answer: I'm sorry but I don't have access to that information.

'''

suffix1 = '''Begin!

Conversation history:
{context}

Question: {input}
{agent_scratchpad} 
'''

suffix1 = temp1 + suffix1

prompt1 = ZeroShotAgent.create_prompt(
    tool1,
    prefix=prefix1,
    suffix=suffix1,
    input_variables=["input", "context", "agent_scratchpad"],
)


class MyCustomHandler(BaseCallbackHandler):
    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        """Run when tool starts running."""
        if serialized['name'] == 'human':
            reply = requests.post("http://localhost:5000/agent", data={"msg": "agent_msg:" + input_str})
            print("\n")
            print(reply.text)
            # print(input_str)

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        """Run on agent end."""
        reply = requests.post("http://localhost:5000/agent",
                              data={"msg": "agent_msg:" + finish.return_values['output']})

class Agent:
    def __init__(self):
        self.llm_chain1 = LLMChain(llm=llm3, prompt=prompt1)
        cb = MyCustomHandler()

        self.agent1 = ZeroShotAgent(llm_chain=self.llm_chain1, tools=tool1, verbose=True,
                               stop=["\nObservation:", "<|im_end|>", "<|im_sep|>"])
        self.history1 = ConversationBufferWindowMemory(k=3, memory_key="context", human_prefix='User', ai_prefix='Assistant')
        self.agent_chain1 = AgentExecutor.from_agent_and_tools(
            agent=self.agent1,
            tools=tool1,
            verbose=True,
            handle_parsing_errors="True",
            memory=self.history1
        )

    def run1(self, query):
        return self.agent_chain1.run(input=query, callbacks=[MyCustomHandler()])


