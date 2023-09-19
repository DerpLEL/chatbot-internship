import datetime
from typing import Any, Dict
import numpy as np
import parsedatetime
from langchain.agents import ZeroShotAgent, AgentExecutor, Tool
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chains import LLMChain
from langchain.chat_models import AzureChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import AgentFinish
from .customHuman import *
from .message import *
import pprint

dtime = datetime.datetime
timedelta = datetime.timedelta

llm3 = AzureChatOpenAI(
    openai_api_type="azure",
    openai_api_base='https://openai-nois-intern.openai.azure.com/',
    openai_api_version="2023-03-15-preview",
    deployment_name='gpt-35-turbo-16k',
    openai_api_key='400568d9a16740b88aff437480544a39',
    temperature=0.0,
    max_tokens=1000,
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


def datetime_calc(query: str):
    # try:
    #     return eval(query)
    # except Exception:
    #     return exec(query)

    cal = parsedatetime.Calendar()
    parsed_date, _ = cal.parseDT(query)

    if parsed_date:
        return parsed_date.strftime("%Y-%m-%d")
    else:
        return "Cannot parse given relative datetime."


def class_chat_input(query, msg: MessageClass):
    msg.output = query

    while not msg.input:
        pass

    res = msg.input
    msg.reset()

    return res


class MyCustomHandler(BaseCallbackHandler):
    prev_msg = ""
    msg: MessageClass = None
    tools = None
    get_appli = False

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        """Run when tool starts running."""
        if serialized['name'] in ['human']:
            # reply = requests.post(f"{addr}/agent", data={"msg": self.prev_msg + input_str},
            #                       timeout=15)
            self.msg.output = self.prev_msg + input_str
            self.prev_msg = ""
            # print("\n")
            # print(reply.text)
            # print(input_str)

        if serialized['name'] == 'HRM get applications':
            # self.prev_msg = self.tools.get_leave_applications()
            # if self.prev_msg == "This user hasn't submitted any leave applications.":
            #     self.prev_msg = ""
            self.get_appli = True

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        """Run on agent end."""
        self.msg.output = self.prev_msg + finish.return_values['output']
        self.prev_msg = ""

    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        """Run when tool ends running."""
        if self.get_appli:
            self.prev_msg = output
            self.get_appli = False

    def set_message(self, obj: MessageClass):
        self.msg = obj

    def set_tools(self, obj):
        self.tools = obj


class Toolset:
    def __init__(self, email, msg):
        self.email = email
        self.msg = msg

        self.human_inp = HumanInputRun()
        self.human_inp.set_msg(self.msg)

        self.token = None

    def set_token(self, token):
        self.token = token
        self.header = {"Authorization": f"Bearer {self.token}"}

    def post_method(self, user_id, manager, start_date, end_date, leave_type, note):
        typeOfLeave = {"paid": 1, "unpaid": 2, "sick": 8, "social insurance": 9, "conference": 5, "other": 3, }
        typeOfPeriod = {"0": "All day", "1": "Morning", "2": "Afternoon"}

        start_dtime = dtime.strptime(start_date, "%Y-%m-%d")
        end_dtime = dtime.strptime(end_date, '%Y-%m-%d')

        manager_id = manager[0]

        num_days = 0
        period = "0"

        if end_dtime == start_dtime:
            period = class_chat_input(
                "Bạn muốn nghỉ buổi nào, bấm theo danh sách số dưới đây:\n0. Cả ngày\n1. Buổi sáng\n2. Buổi chiều\n\n", self.msg)

            while period != "0" and period != "1" and period != "2":
                period = class_chat_input(
                    "Giá trị nhập sai. bấm theo danh sách số dưới đây:\n0. Cả ngày\n1. Buổi sáng\n2. Buổi chiều\n", self.msg)

            num_days = 0.5

            if period == "0":
                num_days = 1

        else:
            num_days = int(np.busday_count(start_date, end_date)) + 1

        string = f'''Chi tiết đơn nghỉ:
            - Người duyệt: {manager[1]}
            - Ngày bắt đầu: {start_date}
            - Ngày kết thúc: {end_date}
            - Hình thức nghỉ: {typeOfLeave[leave_type]} ({leave_type})
            - Số ngày nghỉ: {num_days}
            - Buổi nghỉ: {period} ({typeOfPeriod[period]})
            - Ghi chú (lý do): {note}
        Thông tin này đã chính xác chưa ạ? Bấm 1 để nộp đơn, bấm 0 để chỉnh sửa hoặc hủy.\n'''

        user_confirm = class_chat_input(string, self.msg)

        while user_confirm != "1" and user_confirm != "0":
            user_confirm = class_chat_input("Giá trị nhập sai. Bấm 1 để nộp đơn, bấm 0 để chỉnh sửa hoặc hủy.\n", self.msg)

        if user_confirm.strip() != "1":
            user_edit = class_chat_input("Cho tôi biết bạn muốn chỉnh thông tin gì, hoặc là hủy đơn.\n", self.msg)

            return "User feedback: " + user_edit

        response = requests.post('https://api-hrm.nois.vn/api/leaveapplication', json={
            # "userId": user_id,
            "reviewUserId": manager_id,
            "fromDate": dtime.strftime(start_dtime, "%m/%d/%Y"),
            "toDate": dtime.strftime(end_dtime, "%m/%d/%Y"),
            "leaveApplicationTypeId": typeOfLeave[leave_type],
            "leaveApplicationNote": note,
            "periodType": int(period),
            # "numberOffDay": num_days
        }, headers=self.header)

        try:
            return response.json()['message']

        except KeyError:
            return response.text

    def submitLeaveApplication(self, args: str):
        global lst
        lst = args.split(', ')
        date = dtime.now().strftime("%Y-%m-%d")

        def get_userId(string):
            return string

        def check_manager_name(lst):
            return -1, "None"

        lst = [get_userId(self.email)] + lst

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

        if lst[4] not in ["unpaid", "paid", "sick", "social insurance", "conference", "other"]:
            return "Invalid leave type. Ask the user for the correct type of leave"

        elif lst[4] in ["paid", "sick", "other (wedding or funeral)"]:
            requested_day_off = int(np.busday_count(lst[2], lst[3])) + 1

            remaining_day_off = self.dayoff_allow()

            if remaining_day_off < requested_day_off:
                return f"""User does not have enough remaining day off for this application. Put these information into your question:
    Requested leave day(s): {requested_day_off}
    Remaining leave day(s): {remaining_day_off}
    And ask the user (using the tool human) if they want to apply for a different type, change start or end dates, or cancel."""

        print("\nUserId: ", lst[0], " (", self.email, ")")
        print("ReviewerId: ", manager_id)
        print("Start date: ", lst[2])
        print("End date: ", lst[3])
        print("Type of leaving: ", lst[4])
        print("Note: ", lst[5])

        reply = self.post_method(lst[0], (manager_id, manager_name), lst[2], lst[3], lst[4], lst[5])

        return reply

    def dayoff_allow(self):
        response = requests.get("https://api-hrm.nois.vn/api/user/me", headers=self.header).json()['data']
        return response['maxDayOff'] - response['offDay']

    def get_leave_applications(self, query: str = None):
        # userId = get_userId(self.email)

        applis = requests.get("https://api-hrm.nois.vn/api/leaveapplication/paging?pageIndex=0&pageSize=50&type=0",
                              headers=self.header).json()['data']['items']
        if not applis:
            return "This user hasn't submitted any leave applications."

        #     applis = [i for i in applis if i['reviewStatusName'] != "Đồng ý"]

        string = ""
        counter = 1

        for i in applis:
            string += f"Đơn nghỉ {counter}:\n"
            string += f"ID: {i['id']}\n"
            string += f"Ngày bắt đầu: {i['fromDate']}\n"
            string += f"Ngày kết thúc: {i['toDate']}\n"
            string += f"Hình thức nghỉ: {i['leaveApplicationType']}\n"
            string += f"Số ngày xin nghỉ: {i['numberDayOff']}\n\n"

            counter += 1

        return string

    def delete_leave_applications(self, target: str = "Default"):
        applis = requests.get('https://api-hrm.nois.vn/api/leaveapplication/paging?pageIndex=0&pageSize=50&type=0',
                              headers=self.header).json()['data']['items']

        appli = []

        if ', ' in target:
            target = target.split(', ')
            # appli = [i for i in applis if i['id'] in target]
            for i in applis:
                if i['id'] in target:
                    appli.append(i)

            notify = "Bạn có chắc chắn muốn xóa những đơn nghỉ này? "

        else:
            # appli = [i for i in applis if i['id'] == target]
            for i in applis:
                if i['id'] == target:
                    appli.append(i)

            notify = "Bạn có chắc chắn muốn xóa đơn nghỉ này? "

        string = ""
        for i in appli:
            string += f"ID: {i['id']}\n"
            string += f"Ngày bắt đầu: {i['fromDate']}\n"
            string += f"Ngày kết thúc: {i['toDate']}\n"
            string += f"Hình thức nghỉ: {i['leaveApplicationType']}\n"
            string += f"Số ngày xin nghỉ: {i['numberDayOff']}\n\n"

        inp = class_chat_input(
            string + notify + "Bấm 1 để xóa, bấm 0 để hủy.\n", self.msg).strip()

        while inp != "1" and inp != "0":
            inp = class_chat_input("Giá trị nhập sai, Bấm 1 để xóa, bấm 0 để hủy.\n", self.msg)

        if inp == "0":
            return "User has cancelled the deletion process."

        if isinstance(target, list):
            string = ""
            for i in target:
                print(requests.delete(f"https://api-hrm.nois.vn/api/leaveapplication/{i}",
                                      headers=self.header).json()['message'])
                string += f"Leave application {i}'s deletion: OK\n"

            return string

        return requests.delete(f"https://api-hrm.nois.vn/api/leaveapplication/{target}",
                               headers=self.header).json()['message']

    def get_user_by_email(self, query: str = None):
        user_email = self.email
        if '@' in query and query != user_email:
            return f"Access denied, only the data of the current user {user_email} can be accessed."

        response = requests.get("https://api-hrm.nois.vn/api/user/me", headers=self.header)

        if response.status_code == 200:
            return_text = "User info:\n"
            user_data = response.json()['data']

            for i in user_data.items():
                return_text += f"- {i[0]}: {i[1]}\n"
                if i[0] == "maxDayOff":
                    # remaining_day_off = requests.get(url + f'/api/User/dayoff-data?email={user_email}').json()['data'][
                    #     'dayOffAllow']
                    # return_text += f"- remainingDayOff: {remaining_day_off}\n"
                    return_text += f"- remainingDayOff: {user_data['maxDayOff'] - user_data['offDay']}\n"

            return return_text

        return f'Error: {response.status_code}'

    def book_meeting(self, query: str = None):
        """Prototype meeting function, only takes in members"""
        lst = query.split(', ')

        meeting_header = {
            'Authorization': f'Bearer {self.token}',
            'Content-type': 'application/json',
        }

        meeting_members = []

        # Get member from string input
        email_list = lst[2:]
        if self.email not in email_list:
            email_list = [self.email] + email_list

        for i in email_list:
            temp = dict()
            temp['emailAddress'] = dict()
            temp['emailAddress']['address'] = i
            temp['type'] = 'required'

            meeting_members.append(temp)

        # start = dtime.now()
        # start = start + timedelta(hours=2)
        # end = start + timedelta(hours=2)

        # start.strftime("%Y-%m-%dT%X")
        # end.strftime("%Y-%m-%dT%X")

        x = requests.post(
            'https://graph.microsoft.com/v1.0/me/events',
            headers=meeting_header,
            json={
                "subject": "Test meeting",
                "start": {
                    "dateTime": lst[0],
                    "timeZone": "Asia/Bangkok"
                },
                "end": {
                    "dateTime": lst[1],
                    "timeZone": "Asia/Bangkok"
                },
                "location": {
                    "displayName": "Hong Bang (Factory 1 - Conf. Room)"
                },
                "attendees": meeting_members
            }
        )

        print()
        print(x.status_code)

        if x.status_code == 201:
            meeting_info = x.json()
            # pprint.pprint(meeting_info)

            # f"Meeting created successfully. Meeting details: {x.text}"
            return f"""Meeting created successfully. Relay these meeting info to the user:
- Meeting subject: {meeting_info['subject']}
- Timezone: {meeting_info['originalStartTimeZone']}
- Start: {meeting_info['start']['dateTime']}
- End: {meeting_info['end']['dateTime']}
- Attendees: {email_list}
- Location: {meeting_info['location']['displayName']}"""

    def get_tool1(self):
        return [
            Tool(
                name='HRM get user data',
                func=self.get_user_by_email,
                description='useful for getting data of the current user, data include fullName, birthday, bankAccountNumber, etc. This tool does not take any inputs.'
            ),

            self.human_inp
        ]

    def get_tool2(self):
        return [
            Tool(name='HRM submit leave',
                 func=self.submitLeaveApplication,
                 description=f'''useful for submitting a leave applications for current user.
Input of this tool must include 5 parameters concatenated into a string separated by a comma and space, which are: 
1. manager's name: ask user the name of the manager.
2. start date: ask the user when they want to start their leave and infer the date from the user's answer.
3. end date: ask the user when they want to end their leave and infer the date from the user's answer.
4. type of leave: ask the user what type of leave they want to apply for, there are only 6 types of leave: paid, unpaid, sick, social insurance, conference and other (wedding or funeral).
5. note: ask the user whether they want to leave a note for the manager. Default value is "None".
Until this tool returns "OK", the user's leave application IS NOT submitted.'''
            ),

            Tool(
                name='Calculate relative time',
                func=datetime_calc,
                description=f'useful for calculating relative time inputs (i.e this Tuesday, next Tuesday, this Friday, next Friday, etc). Input is a relative time string and must be in English.'
            ),

            Tool(
                name='HRM get applications',
                func=self.get_leave_applications,
                description='useful for getting leave applications of the current user, mostly for deletion tasks. Input is a "None" string.'
            ),

            Tool(
                name='HRM delete leave application',
                func=self.delete_leave_applications,
                description='useful for deleting specific leave application(s). Input is the ID of the leave application, if the user requests to delete multiple applications, separate them by a comma and space. Always use the tool HRM get applications first and ASK the user which application they want to delete.'
            ),

            self.human_inp
        ]

    def get_tool3(self):
        return [
            Tool(
                name='Book meeting',
                func=self.book_meeting,
                description="""useful for booking a meeting. Input, separated by comma and space, includes the following:
1. Start date and time: format is YYYY-MM-DDThh:mm:ss (T is a separator)
2. End date and time: format is YYYY-MM-DDThh:mm:ss (T is a separator)
3. Participants' emails: can be one or many"""
            ),

            Tool(
                name='Calculate relative time',
                func=datetime_calc,
                description=f'useful for calculating relative time inputs (i.e this Tuesday, next Tuesday, this Friday, next Friday, etc). Input is a relative time string and must be in English.'
            ),

            self.human_inp
        ]


class Agent:
    def __init__(self, user):
        date2 = dtime.strftime(dtime.today(), "%A %Y-%m-%d")

        self.email = user['mail']
        self.name = user['displayName']

        self.msg = MessageClass()
        self.tools = Toolset(self.email, self.msg)

        self.prefix1 = f"""You are an intelligent assistant helping user find his/her information in HRM system by using tool. 
The user chatting with you is {self.name} with the email {self.email}. If question/data are not about them, tell them you don't have access.
DO NOT use data of the user {self.email} to answer questions about other users.
You have access to the following tools:"""

        self.temp1 = f'''

Examples: 
Question: What is my date of birth?
Thought: The user chatting with me has the email {self.email}.
Thought: find the data of user by user's email.
Action: HRM get user data
Action Input: {self.email}
Observation: ...
Thought: I now know the final answer
Final Answer: Your date of birth is ...

Question: What is hung.bui@nois.vn's bank account number?
Thought: The user chatting with me is {self.name} with the email {self.email}.
Thought: the question is not about the current user, so I can't answer the question.
Final Answer: I'm sorry but I don't have access to that information.

'''

        self.suffix1 = '''Begin!

Conversation history:
{context}

Question: {input}
{agent_scratchpad} 
'''

        self.suffix1 = self.temp1 + self.suffix1

        self.prompt1 = ZeroShotAgent.create_prompt(
            self.tools.get_tool1(),
            prefix=self.prefix1,
            suffix=self.suffix1,
            input_variables=["input", "context", "agent_scratchpad"],
        )

        self.prefix2 = f"""You are an intelligent assistant who helps user submit or delete leave applications through the HRM system using tools. 
The user chatting with you has the email: {self.email}. 
Suppose the current date is {date2} (Weekday Year-Month-Day).
You have access to the following tools:"""

        self.temp3 = f'''

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

        self.temp_vnese = f'''

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
Question: Tôi muốn nộp đơn nghỉ phép. Kì nghỉ phép của tôi kết thúc vào 2023-08-18, tôi muốn nghỉ có lương, không cần cung cấp lý do.
Thought: User wants to submit a leave application that ends on 2023-08-18. They are applying for paid leave, with no notes. Manager's name and start date are not provided.
First I will ask the user for the manager's name. Then I will ask the user for the start date.
Action: human
Action Input: Quản lý của bạn là ai?
Observation: đào minh sáng
Thought: The manager is đào minh sáng. I need to ask the user for the start date.
Action: human
Action Input: Bạn muốn bắt đầu nghỉ phép khi nào? (Cung cấp dưới dạng Năm-Tháng-Ngày nếu được)
Observation: 17-08
Thought: The user wants to start their leave on 2023-08-17. Since I have all the required information, I can try submitting the application.
Action: HRM submit leave
Action Input: đào minh sáng, 2023-08-17, 2023-08-18, paid, None
Observation: OK
Thought: I now know the final answer
Final Answer: Đã nộp đơn nghỉ phép thành công

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

        self.suffix2 = """Some steps in the example can be skipped if the user provides enough information.
Ask the user for any missing information.
Remember to use Vietnamese for your questions to the human if the original question is in Vietnamese,
and use English for your questions to the human if the original question is in English!
Begin!

{context}
Question: {input}
Thought: {agent_scratchpad} 
"""

        self.suffix2 = self.temp_vnese + self.suffix2

        self.prompt2 = ZSAgentMod.create_prompt(
            self.tools.get_tool2(),
            prefix=self.prefix2,
            format_instructions=format_instr,
            suffix=self.suffix2,
            input_variables=["input", "context", "agent_scratchpad"],
        )

        self.llm_chain1 = LLMChain(llm=llm3, prompt=self.prompt1)

        self.agent1 = ZSAgentMod(llm_chain=self.llm_chain1, tools=self.tools.get_tool1(), verbose=True,
                                 stop=["\nObservation:", "<|im_end|>", "<|im_sep|>"])
        # self.history1 = ConversationBufferWindowMemory(k=3, memory_key="context", human_prefix='User', ai_prefix='Assistant')
        self.agent_chain1 = AgentExecutor.from_agent_and_tools(
            agent=self.agent1,
            tools=self.tools.get_tool1(),
            verbose=True,
            handle_parsing_errors="True",
            # memory=self.history1
        )

        self.llm_chain2 = LLMChain(llm=llm3, prompt=self.prompt2)
        # self.history2 = ConversationBufferWindowMemory(k=3, memory_key="context", human_prefix='User', ai_prefix='Assistant')

        self.agent2 = ZSAgentMod(llm_chain=self.llm_chain2, tools=self.tools.get_tool2(), verbose=True,
                                 stop=["\nObservation:", "<|im_end|>", "<|im_sep|>"])
        self.agent_chain2 = AgentExecutor.from_agent_and_tools(
            agent=self.agent2,
            tools=self.tools.get_tool2(),
            verbose=True,
            handle_parsing_errors="True",
            # memory=self.history2
        )

        # Suppose the current date is {date2} (Weekday Year-Month-Day).
        self.prefix_meeting = f"""You are an intelligent agent who can book meetings based on users' requests.
You have access to the following tools:"""

        self.meeting_example = """
        
======
Example
Question: I want to book a meeting, today is July 1st, 2001.
Thought: I need to ask the user for the start date and time.
Action: human
Action Input: When do you want the meeting to start?
Observation: July 2nd, 2001 at 9:00am
Thought: Meeting start date and time is 2001-07-02|09:00:00. Now I need to ask the user for the end date and time.
Action: human
Action Input: When do you want to the meeting to end?
Observation: 2 hours after the starting.
Thought: Meeting end date and time is 2001-07-02|11:00:00. Now I need to ask the user for the list of participants.
Action: human
Action Input: Can you please provide the emails of the participants?
Observation: Their emails are abc@gmail.com and 123@hotmail.com
Thought: I have all the required information, now I can book the meeting.
Action: Book meeting
Action Input: 2001-07-02|09:00:00, 2001-07-02|11:00:00, abc@gmail.com, 123@hotmail.com
Observation: Meeting created successfully.
Thought: I now know the final answer
Final Answer: The meeting has been booked successfully.
======

"""

        self.suffix_meeting = """Ask the user for any missing information.
Begin!

Question: {input}
Thought: {agent_scratchpad}
"""

        self.suffix_meeting = self.meeting_example + f"Suppose the current date is {date2} (Weekday Year-Month-Day). " + self.suffix_meeting

        self.prompt_meeting = ZSAgentMod.create_prompt(
            self.tools.get_tool3(),
            prefix=self.prefix_meeting,
            format_instructions=format_instr,
            suffix=self.suffix_meeting,
            input_variables=["input", "agent_scratchpad"],
        )

        self.llm_chain3 = LLMChain(llm=llm3, prompt=self.prompt_meeting)
        # self.history2 = ConversationBufferWindowMemory(k=3, memory_key="context", human_prefix='User', ai_prefix='Assistant')

        self.agent3 = ZSAgentMod(llm_chain=self.llm_chain3, tools=self.tools.get_tool3(), verbose=True,
                                 stop=["\nObservation:", "<|im_end|>", "<|im_sep|>"])
        self.agent_chain3 = AgentExecutor.from_agent_and_tools(
            agent=self.agent3,
            tools=self.tools.get_tool3(),
            verbose=True,
            handle_parsing_errors="True",
            # memory=self.history2
        )

        self.callback = MyCustomHandler()
        self.callback.set_message(self.msg)
        self.callback.set_tools(self.tools)

    def run_hrm(self, query, token):
        # self.history1.clear()
        self.tools.set_token(token)
        return self.agent_chain1.run(input=query, callbacks=[self.callback])

    def run_leave_application(self, query, token):
        # self.history2.clear()
        self.tools.set_token(token)
        return self.agent_chain2.run(input=query, callbacks=[self.callback])

    def run_meeting(self, query, token):
        self.tools.set_token(token)
        return self.agent_chain3.run(input=query, callbacks=[self.callback])
