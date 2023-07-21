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
from customHuman import *
import parsedatetime


llm3 = AzureChatOpenAI(
    openai_api_type="azure",
    openai_api_base='https://openai-nois-intern.openai.azure.com/',
    openai_api_version="2023-03-15-preview",
    deployment_name='text-davinci-003',
    openai_api_key='400568d9a16740b88aff437480544a39',
    temperature=0.0,
    max_tokens=600,
)

format_instr = '''
Structure your response with the following format:

Question: ```the input question you must answer```
Thought: ```you should always think about what to do to answer the input question```
Action: ```the tool you select to use, which should be one of the following: {tool_names}```
Action Input: ```the input to the tool you selected```
Observation: ```the result of the action, this will be computed and given back to you based on your action input```

Repeat the Thought/Action/Action Input/Observation cycle until you find an answer to the Question. 
Then, when you have the final answer to the question, use the following format:

Thought: ```I now know the final answer```
Final Answer: ```your final answer to the original input question```
'''


class ZSAgentMod(ZeroShotAgent):
    @property
    def llm_prefix(self) -> str:
        """Prefix to append the llm call with."""
        return "Thought: "


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
                remaining_day_off = requests.get(url + f'/api/User/dayoff-data?email={user_email}').json()['data']['dayOffAllow']
                return_text += f"- remainingDayOff: {remaining_day_off}\n"

        return return_text

    return f'Error: {response.status_code}'


def output_to_user(query: str = None):
    #     print(query)
    return f'Message "{query}" sent to user.'


def another_chat_input(query):
    reply = requests.post("http://localhost:5000/agent", data={"msg": query})

    res = ""

    while not res:
        reply = requests.get("http://localhost:5000/user").json()
        print(f"Reply: {reply}")
        res = reply['msg']

    print(f"Message: {res} received.")
    return res


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
    if not applis:
        return "This user hasn't submitted any leave applications."

    #     applis = [i for i in applis if i['reviewStatusName'] != "Đồng ý"]

    string = ""
    counter = 1

    for i in applis:
        string += f"Leave application {counter}:\n"
        string += f"ID: {i['id']}\n"
        string += f"Start date: {i['fromDate']}\n"
        string += f"End date: {i['toDate']}\n"
        string += f"Type of leave: {i['leaveApplicationType']}\n"
        string += f"Number of requested leave day(s): {i['numberDayOff']}\n\n"

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
        string += f"Type of leave: {i['leaveApplicationType']}\n"
        string += f"Number of requested leave day(s): {i['numberDayOff']}\n\n"

    inp = another_chat_input(
        string + "Are you sure you want to delete this application? Type 1 to proceed with delete, type 0 to cancel.\n").strip()

    while inp != "1" and inp != "0":
        inp = another_chat_input("Invalid input. Type 1 to proceed with delete, type 0 to cancel.\n")

    if inp == "0":
        return "User has cancelled the deletion process."

    return requests.delete(url + f'/api/LeaveApplication/{target}').json()['message']


def check_manager_name(name):
    response = requests.get(url + '/api/User/manager-users').json()['data']

    for data in response:
        if data['fullName'].lower() == name.lower():
            return data['id'], data['fullName']

    return -1, "Not found"


# def check_manager_id(managerId):
#     response = requests.get(url + '/api/User/manager-users').json()['data']
#
#     for data in response:
#         if data['id'] == int(managerId):
#             return True
#
#     return False


def post_method(user_id, manager, start_date, end_date, leave_type, note):
    typeOfLeave = {"paid": 1, "unpaid": 2, "sick": 8}
    typeOfPeriod = {"0": "All day", "1": "Morning", "2": "Afternoon"}

    start_dtime = dtime.strptime(start_date, "%Y-%m-%d")
    end_dtime = dtime.strptime(end_date, '%Y-%m-%d')

    manager_id = manager[0]

    num_days = 0
    period = "0"

    if end_dtime == start_dtime:
        period = another_chat_input(
            "Which period do you want to leave? Type only the number respectively:\n0. All day\n1. Only the morning\n2. Only the afternoon\n\n")

        while period != "0" and period != "1" and period != "2":
            period = another_chat_input("Invalid input. Type only the number respectively:\n0. All day\n1. Only the morning\n2. Only the afternoon\n")

        num_days = 0.5

        if period == "0":
            num_days = 1

    else:
        num_days = int(np.busday_count(start_date, end_date)) + 1

    string = f'''Leave application details:
    - Manager: {manager[1]}
    - Start date: {start_date}
    - End date: {end_date}
    - Type of leave: {typeOfLeave[leave_type]} ({leave_type})
    - Number of day(s) off: {num_days}
    - Requested leave period: {period} ({typeOfPeriod[period]})
    - Notes: {note}
Is this information correct? Type 1 to submit, type 0 if you want to tell the bot to edit the form.\n'''

    user_confirm = another_chat_input(string)

    while user_confirm != "1" and user_confirm != "0":
        user_confirm = another_chat_input("Invalid input. Type 1 to submit, type 0 if you want to tell the bot to edit the form.\n")

    if user_confirm.strip() != "1":
        user_edit = another_chat_input("Tell the bot what you want to edit in the form.\n")

        return "User feedback: " + user_edit

    response = requests.post('https://hrm-nois-fake.azurewebsites.net/api/LeaveApplication/Submit', json={
        "userId": user_id,
        "reviewUserId": manager_id,
        "relatedUserId": "",
        "fromDate": dtime.strftime(start_dtime, "%m/%d/%Y"),
        "toDate": dtime.strftime(end_dtime, "%m/%d/%Y"),
        "leaveApplicationTypeId": typeOfLeave[leave_type],
        "leaveApplicationNote": note,
        "periodType": int(period),
        "numberOffDay": num_days
    })

    try:
        return response.json()['message']

    except KeyError:
        print(response.text)
        return "OK"


lst = []


# def sickday_allow():
#     response = requests.get(url + f'/api/User/dayoff-data?email={email}').json()['data']
#     return response['sickDayOffAllow']


def dayoff_allow():
    response = requests.get(url + f'/api/User/dayoff-data?email={email}').json()['data']
    return response['dayOffAllow']


def submitLeaveApplication(args: str):
    global lst
    lst = args.split(', ')

    lst = [get_userId(email)] + lst

    if len(lst) != 6:
        return "Incorrect number of arguments, this function requires 5 arguments: manager's id, start date, end date, leave type and note."

    manager_id, manager_name = check_manager_name(lst[1])
    if manager_id == -1:
        return "Ask the user for the correct manager's name. The user either didn't give you a name or gave you the wrong name."

    if '-' not in lst[2]:
        '''Ask the user when they want to start their leave. '''
        return "Infer the date based on the user's answer. Use a tool if possible."

    if dtime.strptime(lst[2], "%Y-%m-%d") < dtime.strptime(date, "%Y-%m-%d"):
        return "Start date cannot be earlier than current date, ask the user for another date."

    if dtime.strptime(lst[2], "%Y-%m-%d").weekday() in [5, 6]:
        return "Start date cannot be on the weekend, ask the user for another date."

    if '-' not in lst[3]:
        '''Ask the user when they want to end their leave. '''
        return "Infer the date based on the user's answer. Use a tool if possible."

    if dtime.strptime(lst[3], "%Y-%m-%d") < dtime.strptime(lst[2], "%Y-%m-%d"):
        return "End date cannot be earlier than start date, ask the user for another date."

    if dtime.strptime(lst[3], "%Y-%m-%d").weekday() in [5, 6]:
        return "End date cannot be on the weekend, ask the user for another date."

    if lst[4] not in ["unpaid", "paid", "sick"]:
        return "Invalid leave type. Ask the user for the correct type of leave"

    elif lst[4] in ["paid", "sick"]:
        requestedDayOff = int(np.busday_count(lst[2], lst[3])) + 1

        remainingDayOff = dayoff_allow()

        if remainingDayOff < requestedDayOff:
            return f"""User does not have enough remaining day off for this application. Put these information into your question:
Requested leave day(s): {requestedDayOff}
Remaining leave day(s): {remainingDayOff}
And ask the user (using the tool human) if they want to apply for a different type, change start or end dates, or cancel."""

    print("\nUserId: ", lst[0])
    print("ReviewerId: ", manager_id)
    print("Start date: ", lst[2])
    print("End date: ", lst[3])

    reply = post_method(lst[0], (manager_id, manager_name), lst[2], lst[3], lst[4], lst[5])

    return reply


def datetime_calc(query: str):
    # try:
    #     return eval(query)
    # except Exception:
    #     return exec(query)

    cal = parsedatetime.Calendar()
    parsed_date, _ = cal.parseDT(query)

    if parsed_date:
        return parsed_date
    else:
        return "Cannot parse given relative datetime."


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

    Tool(
        name='HRM get applications',
        func=get_leave_applications,
        description='useful for getting leave applications of the current user, mostly for deletion tasks. Input is a "None" string.'
    ),

    HumanInputRun()
]

# human = load_tools(['human'])
# tool1.extend(human)

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

tool2 = [
    # Tool(
    #     name='HRM get userId',
    #     func=get_userId,
    #     description='useful for getting the user\'s id by user\'s email. No need to input'
    # ),

    # Tool(
    #     name='HRM get by name',
    #     func=check_manager_name,
    #     description='useful for getting the manager\'s id by manager\'s name. Input is a manager\'s name.'
    # ),

    Tool(
        name='HRM submit leave',
        func=submitLeaveApplication,
        description=f'''useful for submitting a leave applications for current user.
Input of this tool must include 5 parameters concatenated into a string separated by a comma and space, which are: 
1. manager's name: ask user the name of the manager.
2. start date: ask the user when they want to start their leave and infer the date from the user's answer.
3. end date: ask the user when they want to end their leave and infer the date from the user's answer.
4. type of leave: ask the user what type of leave they want to apply for, there are only 3 types of leave: paid, unpaid and sick.
5. note: ask the user whether they want to leave a note for the manager. Default value is "None".
Until this tool returns "OK", the user's leave application IS NOT submitted.'''
    ),
    #     Tool(
    #         name='End conversation',
    #         func=end_convo,
    #         description="useful for ending a chat conversation at the user's request or when you have accomplished your task."
    #     )

    # Tool(
    #     name='Calculate time',
    #     func=datetime_calc,
    #     description=f'useful for calculating dates. Input is a python code utilizing the datetime library.'
    # ),

    Tool(
        name='Calculate relative time',
        func=datetime_calc,
        description=f'useful for calculating relative time inputs (i.e next Tuesday, next Friday, etc). Input is a relative time string.'
    ),

    Tool(
        name='HRM get applications',
        func=get_leave_applications,
        description='useful for getting leave applications of the current user, mostly for deletion tasks. Input is a "None" string.'
    ),

    Tool(
        name='HRM delete leave application',
        func=delete_leave_applications,
        description='useful for deleting a specific leave application. Input is the ID of the leave application. Always run the HRM get applications first and ask the user which application they want to delete.'
    ),

    HumanInputRun(),
]

# human = load_tools(['human'])
# tool2.extend(human)

f'''If you cannot answer by using only 1 tool, try using other provided tools.
If you cannot get any results from tools, say you don't know.
Do not use any other sources other than the ones you obtain from tools.
Suppose the current date is {date} (Year-Month-Day).'''

date2 = dtime.strftime(dtime.today(), "%A %Y-%m-%d")
# print(date2)
# date2 = "Friday 2024-08-11"

prefix2 = f"""You are an intelligent assistant helping user submit or delete leave applications through the HRM system using tools. 
The user chatting with you has the email: {email}. 
Suppose the current date is {date2} (Weekday Year-Month-Day).
You have access to the following tools:"""

temp2_backup = f'''

Example:  
Question: I'd like to submit leave application.
Thought: The user chatting with you own the email {email}.
Thought: Find the user's id by {email}.
Action: HRM get userId
Action Input: {email}
Observation: {get_userId(email)}

Thought: After having user's id, ask the user for the manager's name.
Action: human
Action Input: What is the name of your manager?
Observation: lý minh quân
Thought: find the manager's id by manager's name.
Action: HRM get by name
Action Input: lý minh quân
Observation: 139

Thought: Ask user the date of starting leave (according the format Year-Month-Day)?
Action: human
Action Inpunt: Let me know when do you want to start your leave?
Observation: 2023-07-17

Thought: Ask user the date of ending leave (according the format Year-Month-Day)?
Action: human
Action Input: How about the date of ending leave?
Observation: 2023-07-18

Thought: Got all details for submitting.
Action: HRM submit leave
Action Input: {get_userId(email)}, 139, 2023-07-17, 2023-07-18
Observation: Successfully submitted.
Thought: Leave application is submitted.
Final Answer: Leave application is submitted.

'''

temp2 = f'''

======
Example 1:
Question: Submit a leave application to trần đăng ninh for me, I'll start on 21.07, my leave ends on the 24th. I'm applying for sick leave, and no notes.
Thought: User wants to submit a leave application to their manager trần đăng ninh. Their leave starts on 2023-07-21 and ends on
2023-07-24. The user is applying for sick leave, no notes necessary. Since I have all the required information, I can try submitting the application.
Action: HRM submit leave
Action Input: trần đăng ninh, 2023-07-21, 2023-07-24, sick, None
Observation: OK
Thought: I now know the final answer
Final Answer: Leave application is submitted.

Example 2:  
Question: I'd like to submit a leave application.
Thought: I need to ask the user for the manager's name.
Action: human
Action Input: Who is your manager?
Observation: lý minh quân
Thought: I need to ask the user when they want to start their leave.
Action: human
Action Input: When do you want to start your leave? (YYYY-MM-DD format is preferred)
Observation: 17.07
Thought: User wants to start their leave on 2023-07-17. Now I need to ask the user when they want to end their leave.
Action: human
Action Input: When will your leave end? (YYYY-MM-DD format is preferred)
Observation: 18/7
Thought: User wants to end their leave on 2023-07-18. Now I need to ask the user what type of leave they want to apply for.
Action: human
Action Input: What type of leave do you want to apply for? There are 3 types: paid, unpaid and sick.
Observation: unpaid
Thought: I need to ask the user for their notes to the manager.
Action: human
Action Input: Do you want to leave any notes for the manager?
Observation: I have to visit my grandmother
Thought: Got all details for submitting.
Action: HRM submit leave
Action Input: lý minh quân, 2023-07-17, 2023-07-18, unpaid, "I have to visit my grandmother"
Observation: OK
Thought: I now know the final answer
Final Answer: Leave application is submitted.
======

'''

temp3 = f'''

======
Example 1:
Question: Submit a leave application to trần đăng ninh for me, I'll start on 21.07, my leave ends on the 24th. I'm applying for sick leave, and no notes.
Thought: User wants to submit a leave application to their manager trần đăng ninh. Their leave starts on 2023-07-21 and ends on
2023-07-24. The user is applying for sick leave, no notes necessary. Since I have all the required information, I can try submitting the application.
Action: HRM submit leave
Action Input: trần đăng ninh, 2023-07-21, 2023-07-24, sick, None
Observation: OK
Thought: I now know the final answer
Final Answer: Leave application is submitted.

Example 2:
Question: I want to submit a leave application. My leave ends on 2023-08-18, my leave will be paid, no notes necessary.
Thought: User wants to submit a leave application that ends on 2023-08-18. They are applying for paid leave, with no notes. Manager's name and start date are not provided.
First I will ask the user for the manager's name. Then I will ask the user for the start date.
Action: human
Action Input: Who is your manager?
Observation: đào minh sáng
Thought: The manager is đào minh sáng. I need to ask the user for the start date.
Action: human
Action Input: When do you want to start your leave? (YYYY-MM-DD format is preferred)
Observation: 17-08
Thought: The user wants to start their leave on 2023-08-17. Since I have all the required information, I can try submitting the application.
Action: HRM submit leave
Action Input: đào minh sáng, 2023-08-17, 2023-08-18, paid, None
Observation: OK
Thought: I now know the final answer
Final Answer: Leave application is submitted.

Example 3:  
Question: I'd like to submit a leave application.
Thought: I need to ask the user for the manager's name.
Action: human
Action Input: Who is your manager?
Observation: lý minh quân
Thought: I need to ask the user when they want to start their leave.
Action: human
Action Input: When do you want to start your leave? (YYYY-MM-DD format is preferred)
Observation: 17.07
Thought: User wants to start their leave on 2023-07-17. Now I need to ask the user when they want to end their leave.
Action: human
Action Input: When will your leave end? (YYYY-MM-DD format is preferred)
Observation: 18/7
Thought: User wants to end their leave on 2023-07-18. Now I need to ask the user what type of leave they want to apply for.
Action: human
Action Input: What type of leave do you want to apply for? There are 3 types: paid, unpaid and sick.
Observation: unpaid
Thought: I need to ask the user for their notes to the manager.
Action: human
Action Input: Do you want to leave any notes for the manager?
Observation: I have to visit my grandmother
Thought: Got all details for submitting.
Action: HRM submit leave
Action Input: lý minh quân, 2023-07-17, 2023-07-18, unpaid, "I have to visit my grandmother"
Observation: OK
Thought: I now know the final answer
Final Answer: Leave application is submitted.
======

'''

suffix2 = """Submission steps in the example can be skipped if the user provides enough information.
Ask the user for any missing information.
Begin!

{context}
Question: {input}
Thought: {agent_scratchpad} 
"""

suffix2 = temp3 + suffix2

prompt2 = ZSAgentMod.create_prompt(
    tool2,
    prefix=prefix2,
    format_instructions=format_instr,
    suffix=suffix2,
    input_variables=["input", "context", "agent_scratchpad"],
)


class MyCustomHandler(BaseCallbackHandler):
    prev_msg = ""

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        """Run when tool starts running."""
        if serialized['name'] in ['human']:
            reply = requests.post("http://localhost:5000/agent", data={"msg": self.prev_msg + input_str})
            self.prev_msg = ""
            print("\n")
            print(reply.text)
            # print(input_str)

        if serialized['name'] == 'HRM get applications':
            self.prev_msg = get_leave_applications()
            if self.prev_msg == "This user hasn't submitted any leave applications.":
                self.prev_msg = ""

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        """Run on agent end."""
        reply = requests.post("http://localhost:5000/agent",
                              data={"msg": self.prev_msg + finish.return_values['output']})
        self.prev_msg = ""

    # def on_tool_end(self, output: str, **kwargs: Any) -> Any:
    #     """Run when tool ends running."""
    #     reply = requests.post("http://localhost:5000/agent",
    #                           data={"msg": output})


class Agent:
    def __init__(self):
        self.llm_chain1 = LLMChain(llm=llm3, prompt=prompt1)

        self.agent1 = ZSAgentMod(llm_chain=self.llm_chain1, tools=tool1, verbose=True,
                                 stop=["\nObservation:", "<|im_end|>", "<|im_sep|>"])
        self.history1 = ConversationBufferWindowMemory(k=3, memory_key="context", human_prefix='User', ai_prefix='Assistant')
        self.agent_chain1 = AgentExecutor.from_agent_and_tools(
            agent=self.agent1,
            tools=tool1,
            verbose=True,
            handle_parsing_errors="True",
            memory=self.history1
        )

        self.llm_chain2 = LLMChain(llm=llm3, prompt=prompt2)
        self.history2 = ConversationBufferWindowMemory(k=3, memory_key="context", human_prefix='User', ai_prefix='Assistant')

        self.agent2 = ZSAgentMod(llm_chain=self.llm_chain2, tools=tool2, verbose=True,
                                 stop=["\nObservation:", "<|im_end|>", "<|im_sep|>"])
        self.agent_chain2 = AgentExecutor.from_agent_and_tools(
            agent=self.agent2,
            tools=tool2,
            verbose=True,
            handle_parsing_errors="True",
            memory=self.history2
        )

    def run1(self, query):
        self.history1.clear()
        return self.agent_chain1.run(input=query, callbacks=[MyCustomHandler()])

    def run2(self, query):
        self.history2.clear()
        return self.agent_chain2.run(input=query, callbacks=[MyCustomHandler()])
