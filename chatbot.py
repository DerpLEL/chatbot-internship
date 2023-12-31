# Declare package and library
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from googlesearch import search
from bs4 import BeautifulSoup
from .user import *
from .post_leave_application import *
from .get_leave_application import * 
from .delete_leave_application import *
import tiktoken
import pandas as pd

# Default for encoding
requests.encoding = 'UTF-8'

# Declare for Azure SQL service
server = 'sql-chatbot-server.database.windows.net'
database = 'sql-chatbot'
username = 'test-chatbot'
password = 'bMp{]nzt1'
driver = '{ODBC Driver 17 for SQL Server}'
conn = pyodbc.connect(f'DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}')
cursor = conn.cursor()

# Declare for Azure Search service
search_endpoint = 'https://search-service01.search.windows.net'
search_key = '73Swa5YqUR5IRMwUIqOH6ww2YBm3SveLv7rDmZVXtIAzSeBjEQe9'

# Declare indexes of Search service
public_index_name = "nois-public-v3-index"
private_index_name = "nois-private-v3-index"
company_regulations_index = "nois-company-regulations-v2-index"
nois_drink_fee_index = "nois-drink-fee-index"
fasf_text_index = "fasf-text-01-index"
fasf_images_index = "fasf-images-index"

# Declare for Storage Account service
account_name = 'acschatbotnoisintern'
account_key = 'ohteFF8/tuPx3K0xtA/oIqXSKpx/MTnM4Ia0CbvLXJT1l0KJajB3zvX8A/DsNE9wm3gUq1TDlwve+AStS3nB0A=='
storage_connection_string = 'DefaultEndpointsProtocol=https;AccountName=acschatbotnoisintern;AccountKey=ohteFF8/tuPx3K0xtA/oIqXSKpx/MTnM4Ia0CbvLXJT1l0KJajB3zvX8A/DsNE9wm3gUq1TDlwve+AStS3nB0A==;EndpointSuffix=core.windows.net'
blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)

class chatAI:
# Template to extract keyword 
    keyword_templ = """Below is a history of the conversation so far, and an input question asked by the user that needs to be answered by querying relevant company documents.
Do not answer the question. Output queries must be in both English and Vietnamese and MUST strictly follow this format: (<Vietnamese queries>) | (<English queries>).
Examples are provided down below:

EXAMPLES
Input: Ai là giám đốc điều hành của NOIS?
Ouput: (giám đốc điều hành) | (managing director)
Input: Số người chưa đóng tiền nước tháng 5?
Output: (tiền nước tháng 05 chưa đóng) | (May drink fee not paid)
Input: Ai đã đóng tiền nước tháng 4?
Output: (tiền nước tháng 04 đã đóng) | (April drink fee paid)
Input: Danh sách người đóng tiền nước tháng 3?
Output: (tiền nước tháng 03) | (March drink fee)
Input: Was Pepsico a customer of New Ocean?
Output: Pepsico
Input: What is FASF?
Output: FASF
Input: What is the company's policy on leave?
Ouput: (ngày nghỉ phép) | leave

Chat history:{context}

Question:
{question}
Search query:
"""

# Prompt template for chat (for general)
    chat_template = """<|im_start|>system
Assistant helps the company employees and users with their questions about the companies New Ocean and NOIS. Your answer must adhere to the following criteria:
You MUST follow this rule:
- If question is in English, answer in English. If question is in Vietnamese, answer in Vietnamese. 
- Be brief but friendly in your answers. You may use the provided sources to help answer the question. If there isn't enough information, say you don't know. If asking a clarifying question to the user would help, ask the question.
- If the user greets you, respond accordingly.

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

# First template to classify into different use cases
    classifier_template = """<|im_start|>system
Given a sentence, assistant will determine if the sentence belongs in 1 of 4 categories, which are:
- policy
- drink fee
- hrm
- other

Do not answer the question,     `only output the appropriate category.
**QUESTION REGARDS TO HRM: question related to submitting a leave application, get leave application, 
get user id in hrm and all the same as the one mentioned above.

EXAMPLE
Input: Ai chưa đóng tiền nước tháng 5?
Output: drink fee
Input: Who has paid April 2023 Drink Fee?
Output: drink fee
Input: Quy định công ty về nơi làm việc là gì?
Output: policy
Input: What is Chapter 1, article 2 of the company policy about?
Output: policy
Input: Dịch vụ của NOIS là gì?
Output: other
Input: What is FASF?
Output: other
Input: tôi muốn nộp đơn nghỉ phép?
Output: hrm
Input: tôi muốn xem đơn nhỉ phép của tôi
Output: hrm
Input: tôi còn bao nhiêu ngày nghỉ
Output: hrm
Input: tôi muốn submit ngày nghỉ
Output: hrm
Input: tôi muốn hủy đơn tôi đã submit
Output: hrm
Input: tôi cần thông tin của tôi
Output: hrm
<|im_end|>

Input: {question}
<|im_start|>assistant
Output:"""

# Template for drink fee use case
    drink_fee_template = """<|im_start|>system
Sources:
{summaries}

You must follow these rules:
1. If user require count or ask how many, you must write pandas code for file csv. The output must be 1 line.
2. Output just only code. DO NOT ANSWER THE QUESTION, only code outputs are accepted.
3. Must NO COMMENT, NO RESULT like this "Here is the code to get the list of people who haven't paid for their water bills in May with only their name, email, and status:"
For example:
Input: Danh sách những người đã đóng tiền tháng 5
Output: df[df['Tình trạng'] == Done]
Inpput:có bao nhiêu người có tên là Bảo trong tiền nước tháng 5?
Output: df[df['FullName'].str.contains('BẢO')]['FullName'].count()
Input: có bao nhiêu người có tên là Hiệp đã đóng tiền nước tháng 5?
Output: df[df['Tình trạng'] == 'Done'][df[df['Tình trạng'] == 'Done']['FullName'].str.contains('HIỆP')]['FullName'].count()
Input: Tổng tiền nước tháng 5 đã thu?
Output: df['Đã thu'].sum()
4. You must follow up the structure of dataset.
For example: If ask about fullname is 'Hưng', use must answer with format of dataset is "HƯNG" instead of "hưng" or "Hưng".
<|im_end|>
{context}
<|im_start|>user
{question}
<|im_end|>
<|im_start|>assistant
"""

# Template to classify use case 2 into 2 categories: leave application & user's information
    classifier_hrm = """<|im_start|>system
Given a sentence, assistant will determine if the sentence belongs in 1 of 2 categories, which are:
- LeaveApplication
- User
You answer the question "Is the user's question related to?"
EXAMPLE:
Input: tôi muốn submit ngày nghỉ
Output: LeaveApplication
Input: tôi cần thông tin của tôi
Output: User
Inout: tôi còn bao nhiêu ngày nghỉ phép
Output: LeaveApplication
Input: tôi cần thông tin quản lý của tôi
Output: User
<|im_end|>

Input: {question}
<|im_start|>assistant
Output:"""

# Template to classify leave application tasks into 3 categories: get, post, delete..
    classifier_leave_application = """<|im_start|>system
Given a sentence, assistant will determine if the sentence belongs in 1 of 3 categories, which are:
- get
- post
- delete

You answer the question "Is the user's question related to?"
EXAMPLE:
Input: tôi còn bao nhiêu ngày nghỉ
Output: get
Input: tôi muốn submit ngày nghỉ
Output: post
Input: tôi muốn hủy đơn tôi đã submit
Output: delete
Input: trong năm nay, em đã nghỉ bao nhiêu ngày
Output: get
Input: em nghỉ ngày 7 tháng 7 vì lí do ...
Output: post
Input: em muốn thu hồi đơn xin phép nghỉ ngày 7 tháng 7
Output: delete
Input: tổng ngày nghỉ thai sản mà tôi được phép nghỉ
Output: get
Input: em nghỉ ngày mai buổi sáng
Output: post
Input: tôi muốn rút đơn xin phép nghỉ mà hôm qua tôi đã submit
Output: delete
Input: tổng ngày nghỉ không lương mà tôi được phép nghỉ
Output: get
Input: tôi muốn nghỉ ngày mai vì lí do phải đi khán bệnh
Output: post
Input: tôi muốn rút đơn xin phép nghỉ gần nhất
Output: delete
Input: ngày mai tôi nghỉ
Output: post
Input: tôi muốn nghỉ từ thứ sáu tuần này đến thứ hai tuần sau
Output: post 
<|im_end|>

Input: {question}
<|im_start|>assistant
Output:"""

# Template of deleting application (use case 2)
    delete_custom_template = """ <|im_start|>system
- if the input is "unrelated response to previous question, cancelled previous action", the output, you should say to that same meaning in formal tone and in vietnamese.
- if the input is "Đã xóa thành công", for the output, you shold say that the leave application have been deleted in  vietnamese
- if the input is "empty list", the output should say that the leaving application that awaiting for approval is empty in vietnamese
Input: {question}
<|im_start|>assistant
Output:"""

    def __init__(self):
        # Initial history and private/public mode
        self.history_private = {}
        self.private = False
        # Declare container
        self.container_drink_fee_name = 'nois-drink-fee'
        self.container_client = blob_service_client.get_container_client(self.container_drink_fee_name)

        # Initial bot 1: use for chatting (model gpt-35-turbo-16k of Azure OpenAI)
        self.llm = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='gpt-35-turbo-16k',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.5,
            max_tokens=3000
        )

        # Initial bot 2: use for classification tasks (model gpt-35-turbo-16k of Azure OpenAI)
        self.llm2 = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='gpt-35-turbo-16k',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.7,
            max_tokens=1000
        )

        # Initial bot 3: use for extract keywords & generate pandas code tasks (model gpt-35-turbo-16k of Azure OpenAI)
        self.llm3 = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='gpt-35-turbo-16k',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.0,
            max_tokens=1000
        )

        # Initial Search Service for public data (use case 1)
        self.retriever_public = SearchClient(
            endpoint=search_endpoint,
            index_name=public_index_name,
            credential=AzureKeyCredential(search_key),
            b=0.0,
            k1=0.3,
            searchMode="all"
        )

        # Initial Search Service for private data (use case 1)
        self.retriever_private = SearchClient(
            endpoint=search_endpoint,
            index_name=private_index_name,
            credential=AzureKeyCredential(search_key),
            b=0.0,
            k1=0.3,
            searchMode="all",
        )
        
        # Initial Search Service for drink fee usecase (use case 2)
        self.retriever_drink = SearchClient(
            endpoint=search_endpoint,
            index_name=nois_drink_fee_index,
            credential=AzureKeyCredential(search_key),
            b=0.0,
            k1=0.3,
            searchMode="all",
        )

        # Initial Search Service for company regulations data (use case 1)
        self.retriever_policy = SearchClient(
            endpoint=search_endpoint,
            index_name=company_regulations_index,
            credential=AzureKeyCredential(search_key),
            b=0.0,
            k1=0.3,
            searchMode="all",
        )

        # Call bot to classify and response answer 
        self.qa_chain = load_qa_with_sources_chain(llm=self.llm, chain_type="stuff", prompt=PromptTemplate.from_template(self.chat_template))
        self.keywordChain = LLMChain(llm=self.llm3, prompt=PromptTemplate.from_template(self.keyword_templ))
        self.classifier_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.classifier_template))
        self.drink_chain = load_qa_with_sources_chain(llm=self.llm3, chain_type="stuff", prompt=PromptTemplate.from_template(self.drink_fee_template))

        # For usecase 2
        self.classifier_hrm_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.classifier_hrm))
        # post leave application
        self.leave_application_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.classifier_leave_application))
        self.delete_chat_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.delete_custom_template))
        
    def get_document(self, query, retriever):
        """
            Input: user's query, retriever of index
            Output: document
            Purpsose: Get top 2 documents by search service
        """
        res = retriever.search(search_text=query, top=2)
        doc_num = 1
        doc = []
        for i in res:
            newdoc = Document(page_content=i['content'],
                              metadata={'@search.score': i['@search.score'],
                                        'metadata_storage_name': i['metadata_storage_name'], 'source': f'doc-{doc_num}'})
            doc.append(newdoc)
            doc_num += 1
        return doc


    def update_token(self, token, email):
        """
            Input: user's email, HRM token.
            Output: No output.
            Purpsose: Update token from HRM of user.
        """
        cursor.execute(f"""SELECT token FROM history WHERE email = '{email}';""")
        conv_type = cursor.fetchone()
        print(conv_type)
        token = token.replace("'", "''")

        if not conv_type[0]:
            print(f"Conversation type to be updated to SQL: {token}\n")
            cursor.execute(f"""UPDATE history
                SET token = N'{token}' WHERE email = '{email}';""")
            conn.commit()
            return
        
        print(f"Conversation type to be updated to SQL: {token}\n")
        cursor.execute(f"""UPDATE history
            SET token = N'{token}' WHERE email = '{email}';""")
        conn.commit()
        return
    

    def get_token(self, email):
        """
            Input: user's email.
            Output: No output.
            Purpsose: Get user's token from the database.
        """
        cursor.execute(f"""SELECT token FROM history WHERE email = '{email}';""")
        hist = cursor.fetchone()
        if not hist:
            cursor.execute(f"""INSERT INTO history
    VALUES ('{email}', NULL, NULL, NULL, NULL, NULL, NULL, NULL);""")
            conn.commit()
            return ''

        if not hist[0]:
            return ''
        
        return hist[0]


    def test_token(self, email):
        """
            Input: email get from user.
            Output: True / False.
            Purpose: Check if the token given by user is valid.
        """
        tok = self.get_token(email)
        url = "https://api-hrm.nois.vn/api/user/me"
        header = {"Authorization": f"Bearer {tok}"}

        response = requests.get(url, headers=header)
        response.encoding = 'UTF-8'

        if response.status_code == 200:
            return True

        return False
    

    def login_HRM(self, query, email):
        """
            Input: user's input, email.
            Output: Status line.
            Purpsose: Notify to user the status of login, if not successful, request user to input HRM token.
        """
        token = self.get_token(email)
        url = "https://api-hrm.nois.vn/api/user/me"
        header = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=header)
        response.encoding = 'utf-8'

        if response.status_code == 200:
            return 'Bạn đã đăng nhập thành công vào HRM.'
        else:
            self.update_token(query, email)
            token = self.get_token(email)
            header = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=header)
            response.encoding = 'utf-8'
            
            print(response)
            if response.status_code == 200:
                return "Bạn đã đăng nhập thành công vào HRM."
            else:
                return "Vui lòng nhập lại HRM token."


    def chat_hrm(self, query, email, name):
        """
            Input: user's query, user's email, user's name.
            Output: bot's response.
            Purpsose: Implement tasks in use case 2: user's information and leave application.
        """
        
        if not self.test_token(email):
            self.update_conversation_type(['LeaveApplication', ''], email)
            if self.login_HRM(query, email) == 'Vui lòng nhập lại HRM token.':
                return "Vui lòng nhập lại HRM token."
            elif self.login_HRM(query, email) == 'Bạn đã đăng nhập thành công vào HRM.':
                return "Bạn đã đăng nhập thành công vào HRM."
        token = self.get_token(email)
        print(self.get_conversation_type(email))
        
        # Classify 
        if self.get_conversation_type(email) == ['', ''] or self.get_conversation_type(email) == ['LeaveApplication','']:
            label_hrm = self.classifier_hrm_chain(query)['text']
        else:
            label_hrm = self.get_conversation_type(email)[0]

        response = """"""
        print(label_hrm)

        # User's Information task
        if label_hrm == "User":
            response = run_return_user_response(email, query, token)

        # Leavve application task
        elif label_hrm == "LeaveApplication":
            if self.get_conversation_type(email) == ['',''] or self.get_conversation_type(email) == ['LeaveApplication','']:
                leave_application_type = self.leave_application_chain(query)['text']
            else:
                leave_application_type = self.get_conversation_type(email)[1]

            print(leave_application_type)

            # Get leave applications
            if leave_application_type == 'get':
                response = run_get_leave_application(email, query, token)
            # Submit leave application
            elif leave_application_type == 'post':
                self.update_conversation_type(['LeaveApplication', 'post'], email)
                post_leave_application_response = post_leave_application_func({'username': name, 'mail': email}, query, token, email)
                response = post_leave_application_response[0]
                print(post_leave_application_response)
                try:
                    if post_leave_application_response[1].status_code == 200:
                        self.update_conversation_type(['', ''], email)
                    elif post_leave_application_response[1].status_code == 401:
                        self.update_conversation_type(['', ''], email)
                    elif post_leave_application_response[1].status_code == 100:
                        self.update_conversation_type(['', ''], email)
                except:
                    pass
            # Delete leave application
            elif leave_application_type == 'delete':
                self.update_conversation_type(['LeaveApplication','delete'], email)
                print("delete - pass")
                response = run_leave_application_delete(email, query, "", token)
                if (response =="unrelated response to previous question, cancelled previous action"):
                    self.update_conversation_type(['', ''], email)
                    response = str(self.delete_chat_chain(response)['text'])
                    return response
                elif (response == "Đã xóa thành công" or response == "empty list"):
                    self.update_conversation_type(['', ''], email)
                    response = str(self.delete_chat_chain(response)['text'])
        
        return response
    

    def update_conversation_type(self, conversation_type, email):
        """
            Input: user's email, conversation type.
            Output: No output.
            Purpose: Update the conversation type of user.
        """
        cursor.execute(f"""SELECT conversation_type FROM history WHERE email = '{email}';""")
        conv_type = cursor.fetchone()
        print(conv_type)
        res = str(conversation_type).replace("'", "")

        print(res)
        if not conv_type[0]:
            print(f"Conversation type to be updated to SQL: {res}\n")
            cursor.execute(f"""UPDATE history
                SET conversation_type = N'{res}' WHERE email = '{email}';""")
            conn.commit()
            return
        
        print(f"Conversation type to be updated to SQL: {res}\n")
        cursor.execute(f"""UPDATE history
            SET conversation_type = N'{res}' WHERE email = '{email}';""")
        conn.commit()
        return
    

    def get_conversation_type(self, email):
        """
            Input: user's email.
            Output: the type of conversation. Return null string if there's no type.
            Purpose: check if the conversation now is about leave application 
        """

        cursor.execute(f"""SELECT conversation_type FROM history WHERE email = '{email}';""")
        hist = cursor.fetchone()

        # Define null to all columns of data of user if there is no history
        if not hist:
            cursor.execute(f"""INSERT INTO history
VALUES ('{email}', NULL, NULL, NULL, NULL, NULL, NULL, NULL);""")
            conn.commit()

            return ['','']

        if not hist[0]:
            return ['','']
        
        hist[0] = hist[0].replace("[", "").replace("]", "")
        lst = hist[0].split(",")
        return [s.strip() for s in lst]


    def count_tokens(self, string):
        """
            Input: a string
            Output: numbers of tokens
            Purpose: count the numbers tokens of a string from input. 
        """
        token_encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        return len(token_encoding.encode(string))


    def add_to_history_sql(self, query, response, email):
        """
            Input: user's query, response from bot, user's email.
            Output: No output.
            Purpose: add history of conversations to database. 
        """
        n = 1500
        cursor.execute(f"""SELECT chat FROM history WHERE email = '{email}';""")
        hist = cursor.fetchone()

        if not hist[0]:
            res = f"{query}||{response}".replace("'", "''")

            print(f"History to be updated to SQL: {res}\n")
            cursor.execute(f"""UPDATE history
            SET chat = N'{res}' WHERE email = '{email}';""")
            conn.commit()
            return

        hist = hist[0].split("<sep>")
        hist.append(f"{query}||{response}")
        new_hist = []
        total = 0

        for i in hist[::-1]:
            convo_length = self.count_tokens(i)
            total += convo_length
            if total > n:
                break
            new_hist.append(i)

        res = "<sep>".join(new_hist[::-1]).replace("'", "''")
        print(f"History to be updated to SQL: {res}\n")
        cursor.execute(f"""UPDATE history
        SET chat = N'{res}' WHERE email = '{email}';""")
        conn.commit()
        return
    

    def get_history_as_txt_sql(self, email):
        """
            Input: user's email.
            Output: conversation history of user formatted with txt.
            Purpose: get history data of a user from database and return into txt.
        """
        cursor.execute(f"""SELECT chat FROM history WHERE email = '{email}';""")
        hist = cursor.fetchone()

        # Define null to all columns of data of user if there is no history 
        if not hist:
            cursor.execute(f"""INSERT INTO history
VALUES ('{email}', NULL, NULL, NULL, NULL, NULL, NULL, NULL);""")
            conn.commit()
            return ""

        if not hist[0]:
            return ""

        hist = hist[0].split("<sep>")
        txt = ""

        # Get chat history in pairs of {query, response}
        for row in hist:
            i = row.split('||')
            try:
                txt += f"\n<|im_start|>user\n{i[0]}\n<|im_end|>\n"
                txt += f"<|im_start|>assistant\n{i[1]}\n<|im_end|>"
            except IndexError:
                break

        return txt

    def chat_private(self, query, email, name):
        """
            Input: query from user, user's email, user's name.
            Output: response from bot.
            Purpose: response the answer to user following the label, which identified by classifier. 
        """
        print(self.get_conversation_type(email)[0] == 'LeaveApplication')
        
        # Check if the label is 'hrm' or not
        if str(self.get_conversation_type(email)[0]) == '':
            label = self.classifier_chain({'question': query, 'context': self.get_history_as_txt_sql(email)})['text']
        else:
            label = "hrm"

        print("label " + label)
        keywords = self.keywordChain({'question': query, 'context': self.get_history_as_txt_sql(email)})['text']
        print(keywords)

        chain = self.qa_chain

        # Implement tasks following the label:
        if label == "drink fee":
            doc = self.get_document(keywords, self.retriever_drink)[:1]

            input_pandas = self.drink_chain({'input_documents': doc, 'question': query, 'context': ''}, return_only_outputs=False)

            try:
                blob_name = doc[0].metadata['metadata_storage_name']
            except IndexError:
                return {'output_text': 'Không tìm thấy file tiền nước, bạn vui lòng hỏi lại với đầy đủ thông tin.'}, None
        
            print(input_pandas['output_text']) 
            temp_result = self.excel_drink_preprocess(input_pandas['output_text'], blob_name, doc)
            print(temp_result)
            result_doc = "Input: " + query +"\n Output: " + str(temp_result)
            print(result_doc)

            doc[0].page_content = result_doc

        elif label == "policy":
            doc = self.get_document(keywords, self.retriever_policy)

        elif label == "hrm":
            response = self.chat_hrm(query, email, name)
            return response, " "

        else:  
            doc = self.get_document(keywords, self.retriever_private)
            try:
                num_results = 3
                for result in search(query + "hiện tại", num_results=num_results):
                    response = requests.get(result)
                    html_content = response.text
                    soup = BeautifulSoup(html_content, 'html.parser')

                    for tag in soup.find_all():
                        tag.replace_with(tag.text)

                    text = soup.get_text()
                    doc[0].page_content = text[:4100]
            except:
                pass
        try:
            hist = self.get_history_as_txt_sql(email) if label != 'drink fee' else ''
            response = chain({'input_documents': doc, 'question': query, 'context': hist,
                                'user_info': f'''The user chatting with you is named {name}, with email: {email}. 
                                '''},
                             return_only_outputs=False)

        except Exception as e:
            return {'output_text': f'Cannot generate response, error: {e}'}, doc

        self.add_to_history_sql(query, response['output_text'], email)
        return response, doc


    def excel_drink_preprocess(self, input_pandas, file_name, doc):
        """ 
            Input: file name, doc, input pandas code. 
            Output: pandas file.
            Purpose: get excel file of drink fee and convert into pandas.
        """

        sas_i = generate_blob_sas(account_name = account_name,
                            container_name = self.container_drink_fee_name,
                            blob_name = file_name,
                            account_key=account_key,
                            permission=BlobSasPermissions(read=True),
                            expiry=datetime.utcnow() + timedelta(hours=1))

        sas_url = 'https://' + account_name + '.blob.core.windows.net/' + self.container_drink_fee_name + '/' + file_name + '?' + sas_i

        df = pd.read_excel(sas_url)
        doc[0].page_content = df

        df = pd.read_excel(sas_url, skiprows=1)
        print(df)

        try:
            result_pandas = eval(input_pandas) 
        except Exception as e:
            return input_pandas

        return result_pandas
