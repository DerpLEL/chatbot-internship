from langchain.prompts import PromptTemplate
from langchain.document_transformers import Document
from langchain.chains import LLMChain
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from langchain.llms import AzureOpenAI
from langchain.chat_models import AzureChatOpenAI
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
import pandas as pd
from azure.core.exceptions import ResourceExistsError
from datetime import datetime, timedelta

public_index_name = "nois-public-v3-index"
private_index_name = "nois-private-v3-index"
company_regulations_index = "nois-company-regulations-v2-index"
nois_drink_fee_index = "nois-drink-fee-index"
search_endpoint = 'https://search-service01.search.windows.net'
search_key = '73Swa5YqUR5IRMwUIqOH6ww2YBm3SveLv7rDmZVXtIAzSeBjEQe9'

# os.environ["AZURE_COGNITIVE_SEARCH_SERVICE_NAME"] = "search-service01"
# os.environ["AZURE_COGNITIVE_SEARCH_API_KEY"] = "73Swa5YqUR5IRMwUIqOH6ww2YBm3SveLv7rDmZVXtIAzSeBjEQe9

account_name = 'acschatbotnoisintern'
account_key = 'ohteFF8/tuPx3K0xtA/oIqXSKpx/MTnM4Ia0CbvLXJT1l0KJajB3zvX8A/DsNE9wm3gUq1TDlwve+AStS3nB0A=='
storage_connection_string = 'DefaultEndpointsProtocol=https;AccountName=acschatbotnoisintern;AccountKey=ohteFF8/tuPx3K0xtA/oIqXSKpx/MTnM4Ia0CbvLXJT1l0KJajB3zvX8A/DsNE9wm3gUq1TDlwve+AStS3nB0A==;EndpointSuffix=core.windows.net'
blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)


class chatAI:
    keyword_templ = """Below is a history of the conversation so far, and an input question asked by the user that needs to be answered by querying relevant company documents.
Generate a search query based on the conversation and the new question.Replace AND with + and OR with |. Verbs, adjectives and stop words must be accompanied by |.
Do not answer the question. Output queries must be in both English and Vietnamese and MUST strictly follow this format: (<Vietnamese queries>) | (<English queries>).
Examples are provided down below:

EXAMPLES
Input: Ai là giám đốc điều hành của NOIS?
Ouput: (giám +đốc +điều +hành) | (managing +director)
Input: Số người chưa đóng tiền nước tháng 5?
Output: (tiền +nước +tháng +05 |chưa |đóng) | (May +drink +fee |not |paid)
Input: Ai đã đóng tiền nước tháng 4?
Output: (tiền +nước +tháng +04 |đã |đóng) | (April +drink +fee |paid)
Input: Danh sách người đóng tiền nước tháng 3?
Output: (tiền +nước +tháng +03) | (March +drink +fee)
Input: Was Pepsico a customer of New Ocean?
Output: Pepsico
Input: What is FASF?
Output: FASF
Input: What is the company's policy on leave?
Ouput: (ngày +nghỉ +phép) | leave

Chat history:{context}

Question:
{question}

Search query:
"""

    question_prompt = """Below is a history of the conversation so far, and an input question asked by the user that needs to be answered by querying relevant company documents.
Generate a new question with full context based on the conversation and the given question. Do not answer the question.
Your generated question's language must match the given question's language. Examples are provided below.

EXAMPLE
Current question
Ai chưa đóng tiền nước tháng 5?
Generated question
Ai chưa đóng tiền nước tháng 5?
Current question
Ai đóng rồi?
Generated question
Ai đóng tiền nước tháng 5 rồi?

CONVERSATION HISTORY{context}

CURRENT QUESTION
{question}

GENERATED QUESTION
"""

    backup_chat = """<|im_start|>system
Assistant helps users answer their questions about NOAS and NOIS. Your answer must adhere to the following criteria:
- The info might be spread across 2 documents, so check the docs carefully.
- Be brief but friendly in your answers. If asking a clarifying question to the user would help, ask the question. You may use the sources provided to answer. If you can't find the answer from the sources, say you don't know.
- If question is Vietnamese, answer in Vietnamese, DO NOT answer in English. If question is English, then you may answer in English.
- If the user greets you, respond accordingly. If asked a question not related to NOIS or NOAS, apologize and request another question.

Sources:
{summaries}
<|im_end|>

Chat history:{context}

<|im_start|>user
{question}
<|im_end|>
<|im_start|>assistant
"""

    chat_template = """<|im_start|>system
Assistant helps company employees and users with their questions about the companies New Ocean Automation System and NOIS. Your answer must adhere to the following criteria:
- The info might be spread across 2 documents, so check the docs carefully.
- Be brief and friendly in your answers. Answer ONLY with the facts listed in the list of sources below. If there isn't enough information below, say you don't know. Do not generate answers that don't use the sources below. If asking a clarifying question to the user would help, ask the question.
- If the user asks any questions not related to New Ocean Automation System or NOIS, apologize and request another question from the user. If the user greets you, respond accordingly.
- You must answer in the current question's language.

Sources:
{summaries}
<|im_end|>

Chat history:{context}

Answer in the current question's language.
<|im_start|>user
{question}
<|im_end|>
<|im_start|>assistant
"""

    keyword_templ_drink_fee = """<|im_start|>system
Given a sentence and a conversation about the companies New Ocean and NOIS, assistant will extract keywords based on the conversation and the sentence and translate them to Vietnamese if they're in English and vice versa.
Your output will be on one line, in both languages if possible and separated by commas. Do not duplicate keywords.
Assume the context is about the companies unless specified otherwise. Only return the keywords, do not output anything else.


EXAMPLE
Input: Ai chưa đóng tiền nước tháng 3?
Output: input:Vietnamese
Input: Was Pepsico a customer of New Ocean?
Output: input:English
Input: What is FASF?
Output: input:English
<|im_end|>
{context}
<|im_start|>user
Input: {question}
<|im_end|>
<|im_start|>assistant
Output:"""

    classifier_template = """<|im_start|>system
Given a question and a conversation, assistant will determine based on the question and the conversation history if the question belongs in 1 of 3 categories, which are:
- policy
- drink fee
- other
Do not answer the question, only output the appropriate category.

Chat history:{context}

EXAMPLE
Input: Ai chưa đóng tiền nước tháng 5?
Output: drink fee
Input: Who has paid April 2023 Drink Fee?
Output: drink fee
Input: Quy định công ty về nơi làm việc là gì?
Output: policy
Input: What is Chapter 1, article 2 of the company policy about?
Output: policy
Input: Số ngày làm việc ở nhà?
Output: policy
Input: Dịch vụ của NOIS là gì?
Output: other
Input: What is NOIS?
Output: other
Input: What is FASF?
Output: other
<|im_end|>

Input: {question}
<|im_start|>assistant
Output:"""

    backup_drink = """<|im_start|>system
Sources:
{summaries}

You must follow this rule:
1. If user require count or ask how many, you must write pandas code for file csv. The output must be 1 line.
Your ouput must only include code and nothing else, DO NOT print out the provided sheet.
Must NO COMMENT, NO RESULT, NO ADD anything to the line of code.
For example:
Input:có bao nhiêu người có tên là Bảo trong tiền nước tháng 5?
Output: df[df['FullName'].str.contains('BẢO')]['FullName'].count()
Input: có bao nhiêu người có tên là Hiệp đã đóng tiền nước tháng 5?
Output: df[df['Tình trạng'] == 'Done'][df[df['Tình trạng'] == 'Done']['FullName'].str.contains('HIỆP')]['FullName'].count()
Input: tiền nước tháng 5 bao nhiêu người chưa đóng?
Output: df[df['Tình trạng'] != 'Done']['FullName'].count()

2. You must follow up the structure of dataset.
For example: If ask aboout fullname is 'Hưng', use must answer with format of dataset is "HƯNG" instead of "hưng" or "Hưng"

<|im_end|>
{context}
<|im_start|>user
{question}
<|im_end|>
<|im_start|>assistant
"""

    drink_fee_template = """<|im_start|>system

Sources:
{summaries}

You must follow this rule:
1. If user require count or ask how many, you must write pandas code for file csv. The output must be 1 line.
2. Output just only code.
3. Must NO COMMENT, NO RESULT
For example:
Input: Danh sách những người đã đóng tiền tháng 5
Output: df[df['Tình trạng'] == Done]
Inpput:có bao nhiêu người có tên là Bảo trong tiền nước tháng 5?
Output: df[df['FullName'].str.contains('BẢO')]['FullName'].count()
Input: có bao nhiêu người có tên là Hiệp đã đóng tiền nước tháng 5?
Output: df[df['Tình trạng'] == 'Done'][df[df['Tình trạng'] == 'Done']['FullName'].str.contains('HIỆP')]['FullName'].count()
4. You must follow up the structure of dataset.
For example: If ask aboout fullname is 'Hưng', use must answer with format of dataset is "HƯNG" instead of "hưng" or "Hưng"
<|im_end|>

{context}
<|im_start|>user
{question}
<|im_end|>
<|im_start|>assistant
"""

    def __init__(self):
        self.history_public = []
        self.history_private = []
        self.private = False
        self.container_drink_fee_name = 'nois-drink-fee'
        self.container_client = blob_service_client.get_container_client(self.container_drink_fee_name)

        self.llm = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='test-1',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.5,
            max_tokens=250
        )

        self.llm2 = AzureOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='test-1',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.7,
            max_tokens=600,
            top_p=0.5,
            stop=['<|im_end|>', '\n', '<|im_sep|>']
        )

        self.llm3 = AzureOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='test-1',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.0,
            max_tokens=100,
            stop=['<|im_end|>', '\n', '<|im_sep|>']
        )

        self.retriever_public = SearchClient(
            endpoint=search_endpoint,
            index_name=public_index_name,
            credential=AzureKeyCredential(search_key),
            b=0.0,
            k1=0.3,
            searchMode="all"
        )

        self.retriever_private = SearchClient(
            endpoint=search_endpoint,
            index_name=private_index_name,
            credential=AzureKeyCredential(search_key),
            b=0.0,
            k1=0.3,
            searchMode="all"
        )

        self.retriever_drink = SearchClient(
            endpoint=search_endpoint,
            index_name=nois_drink_fee_index,
            credential=AzureKeyCredential(search_key),
            b=0.0,
            k1=0.3,
            searchMode="all"
        )

        self.retriever_policy = SearchClient(
            endpoint=search_endpoint,
            index_name=company_regulations_index,
            credential=AzureKeyCredential(search_key),
            b=0.0,
            k1=0.3,
            searchMode="all"
        )

        self.qa_chain = load_qa_with_sources_chain(llm=self.llm, chain_type="stuff",
                                                   prompt=PromptTemplate.from_template(self.chat_template))
        self.keyword_chain = LLMChain(llm=self.llm3, prompt=PromptTemplate.from_template(self.keyword_templ))
        self.classifier_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.classifier_template))
        self.drink_chain = load_qa_with_sources_chain(llm=self.llm2, chain_type="stuff",
                                                      prompt=PromptTemplate.from_template(self.drink_fee_template))
        self.question_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.question_prompt))

    def get_document(self, query, retriever, n=4):
        # Get top 3 documents
        res = retriever.search(search_text=query, top=n)

        doc_num = 1
        doc = []
        for i in res:
            newdoc = Document(page_content=i['content'],
                              metadata={'@search.score': i['@search.score'],
                                        'metadata_storage_name': i['metadata_storage_name'],
                                        'source': f'doc-{doc_num}'})

            doc.append(newdoc)
            doc_num += 1

        return doc

    def get_history_as_txt(self):
        txt = ""
        hist = self.history_public

        if self.private:
            hist = self.history_private

        history = hist[::-1]
        for i in history[:3]:
            txt += f"\n<|im_start|>user\n{i['user']}\n<|im_end|>\n"
            txt += f"<|im_start|>assistant\n{i['AI']}\n<|im_end|>"

        return txt

    def add_to_history(self, user_msg, ai_msg):
        hist = self.history_public
        if self.private:
            hist = self.history_private

        hist.append({'user': user_msg, 'AI': ai_msg})

    def chat(self, query):
        if self.private:
            return self.chat_private(query)

        return self.chat_public(query)

    def chat_public(self, query):
        keywords = self.keyword_chain({'question': query, 'context': self.get_history_as_txt()})['text'].strip()
        # keywords = query
        print(f"Query: {query}\nKeywords: {keywords}")

        chain = self.qa_chain
        doc = self.get_document(keywords, self.retriever_public)

        try:
            response = chain({'input_documents': doc, 'question': query, 'context': self.get_history_as_txt()},
                             return_only_outputs=False)
        except Exception as e:
            return {'output_text': f'Cannot generate response, error: {e}'}, doc

        self.add_to_history(query, response['output_text'])
        return response, doc

    def chat_private(self, query):
        label = self.classifier_chain({'question': query, 'context': self.get_history_as_txt()})['text'].strip()
        print(f"Label: {label}")

        # keywords = self.keyword_chain({'question': query, 'context': self.get_history_as_txt()})['text'].strip()
        keywords = query
        # keywords = self.question_chain({'question': query, 'context': self.get_history_as_txt()})['text'].strip()
        print(f"Query: {query}\nKeywords: {keywords}")

        chain = self.qa_chain

        if "drink fee" in label:
            keyword_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.keyword_templ_drink_fee))
            keywords_drink_fee = keyword_chain({'context': self.get_history_as_txt(), 'question': query})
            print(f"Drink fee keywords: {keywords_drink_fee['text']}")

            doc = self.get_document(keywords_drink_fee, self.retriever_drink, 1)

            input_pandas = self.drink_chain(
                {'input_documents': doc, 'question': query, 'context': ''},
                return_only_outputs=False)

            try:
                blob_name = doc[0].metadata['metadata_storage_name']
            except Exception as e:
                return {'output_text': f'Cannot generate response, error: {e}'}, None

            temp_result = self.excel_drink_preprocess(input_pandas['output_text'], blob_name)
            result_doc = "Input: " + query + "\n Output: " + str(temp_result)

            if """count""" not in input_pandas['output_text']:
                return {'output_text': str(temp_result)}, doc

            doc[0].page_content = result_doc

        elif "policy" in label:
            doc = self.get_document(keywords, self.retriever_policy)

        else:
            doc = self.get_document(keywords, self.retriever_private)

        try:
            response = chain({'input_documents': doc, 'question': query, 'context': self.get_history_as_txt()},
                             return_only_outputs=False)
        except Exception as e:
            return {'output_text': f'Cannot generate response, error: {e}'}, doc

        self.add_to_history(query, response['output_text'])
        return response, doc

    def excel_drink_preprocess(self, input_pandas, file_name):
        sas_i = generate_blob_sas(account_name=account_name,
                                  container_name=self.container_drink_fee_name,
                                  blob_name=file_name,
                                  account_key=account_key,
                                  permission=BlobSasPermissions(read=True),
                                  expiry=datetime.utcnow() + timedelta(hours=1))

        sas_url = 'https://' + account_name + '.blob.core.windows.net/' + self.container_drink_fee_name + '/' + file_name + '?' + sas_i

        df = pd.read_excel(sas_url, skiprows=1)
        df = df[df['FullName'].notnull()]
        df = df.iloc[:, df.columns.notna()]

        try:
            result_pandas = eval(input_pandas)
        except Exception as e:
            return {'output_text': f'''Cannot generate response, error: {e}
            Trace: {input_pandas}'''}, None

        return result_pandas

    def clear_history(self):
        self.history_public = []
        self.history_private = []
