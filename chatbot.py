from langchain.prompts import PromptTemplate
from langchain.document_transformers import Document
from azure.core.credentials import AzureKeyCredential
from langchain.chains import LLMChain
from azure.search.documents import SearchClient
from langchain.chat_models import AzureChatOpenAI
from langchain.llms import AzureOpenAI
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.core.exceptions import ResourceExistsError
from datetime import datetime, timedelta

import pandas as pd
import openpyxl
import os

public_index_name = "nois-public-v3-index"
private_index_name = "nois-private-v3-index"
company_regulations_index = "nois-company-regulations-v2-index"
nois_drink_fee_index = "nois-drink-fee-index"
semantic_index = "nois-private-semantic-nonnum-index"
search_endpoint = 'https://search-service01.search.windows.net'
search_key = '73Swa5YqUR5IRMwUIqOH6ww2YBm3SveLv7rDmZVXtIAzSeBjEQe9'

# os.environ["AZURE_COGNITIVE_SEARCH_SERVICE_NAME"] = "search-service01"
# os.environ["AZURE_COGNITIVE_SEARCH_API_KEY"] = "73Swa5YqUR5IRMwUIqOH6ww2YBm3SveLv7rDmZVXtIAzSeBjEQe9

account_name = 'acschatbotnoisintern'
account_key = 'ohteFF8/tuPx3K0xtA/oIqXSKpx/MTnM4Ia0CbvLXJT1l0KJajB3zvX8A/DsNE9wm3gUq1TDlwve+AStS3nB0A=='
storage_connection_string = 'DefaultEndpointsProtocol=https;AccountName=acschatbotnoisintern;AccountKey=ohteFF8/tuPx3K0xtA/oIqXSKpx/MTnM4Ia0CbvLXJT1l0KJajB3zvX8A/DsNE9wm3gUq1TDlwve+AStS3nB0A==;EndpointSuffix=core.windows.net'
blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)

class chatAI:
    keyword_templ_backup = """Below is a history of the conversation so far, and an input question asked by the user that needs to be answered by querying relevant company documents.
Generate a search query based on the conversation and the new question. Use Roman numerals for chapter numbers. Only include the most important queries.
Replace AND with + and OR with |. Do not answer the question.

EXAMPLE
Input: Ai là giám đốc điều hành?
Ouput: (giám +đốc +điều +hành) | (managing +director)
Input: Ai chưa đóng tiền nước tháng 5?
Output: (tiền +nước +tháng +05) | (May +drink +fee)
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

    keyword_templ = """Below is a history of the conversation so far, and an input question asked by the user that needs to be answered by querying relevant company documents.
Generate a search query along with the input language based on the conversation and the new question. The output query must adhere to the following criteria:
- Output query must be in both English and Vietnamese and MUST strictly follow this format: input:<Input language>, (<Vietnamese queries>) | (<English queries>).
- Replace AND with + and OR with |. Do not put queries outside of ().
Examples are provided down below.

Examples:
Input: Ai là giám đốc điều hành của NOIS?
Ouput: input:Vietnamese, (giám đốc điều hành) | (managing director)
Input: Số người chưa đóng tiền nước tháng 5?
Output: input:Vietnamese, (tiền nước tháng 05) | (May drink fee)
Input: Danh sách người đóng tiền nước tháng 3?
Output: input:Vietnamese, (tiền nước tháng 03) | (March drink fee)
Input: Was Pepsico a customer of New Ocean?
Output: input:English, Pepsico
Input: What is FASF?
Output: input:English, FASF
Input: What is the company's policy on leave?
Ouput: input:English, (ngày nghỉ phép) | (leave)

Chat history:{context}

Question:
{question}

Search query:
"""

    '''Input: Số người chưa đóng tiền nước tháng 5?
Output: (tiền +nước +tháng +05 |chưa |đóng) | (May +drink +fee |not |paid)
Input: Ai đã đóng tiền nước tháng 4?
Output: (tiền +nước +tháng +04 |đã |đóng) | (April drink fee paid)'''

    '''Input: Điều 7 chương 2 gồm nội dung gì?
Output: ("điều 7" + "chương II") | ("article 7" + "chapter II")'''

    chat_template = """<|im_start|>system
Assistant helps the company employees and users with their questions about the companies New Ocean and NOIS. Your answer must adhere to the following criteria:
- Be brief but friendly in your answers. You may use the provided sources to help answer the question. If there isn't enough information, say you don't know. If asking a clarifying question to the user would help, ask the question.
- If the user greets you, respond accordingly.
- If question is in English, answer in English. If question is in Vietnamese, answer in Vietnamese

Sources:
{summaries}
<|im_end|>

Chat history:{context}

<|im_start|>user
{question}
<|im_end|>
<|im_start|>assistant
"""

    backup_classifier_template = """Given an input sentence and a history of the conversation so far, determine if the sentence belongs in 1 of 3 categories, which are:
- policy
- drink fee
- other
Do not answer the question, only output the appropriate category.

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

Chat history:{context}

Sentence:
{question}

Output:
"""

    classifier_template = """Given an input sentence and a history of the conversation so far, determine if the sentence belongs in 1 of 3 categories, which are:
- drink fee
- other
Do not answer the question, only output the appropriate category.

EXAMPLE
Input: Ai chưa đóng tiền nước tháng 5?
Output: drink fee
Input: Who has paid April 2023 Drink Fee?
Output: drink fee
Input: Quy định công ty về nơi làm việc là gì?
Output: other
Input: What is Chapter 1, article 2 of the company policy about?
Output: other
Input: Dịch vụ của NOIS là gì?
Output: other
Input: What is FASF?
Output: other

Chat history:{context}

Sentence:
{question}

Output:
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

    def __init__(self):
        self.history_public = []
        self.history_private = []
        self.private = False
        self.container_drink_fee_name = 'nois-drink-fee'
        self.container_client = blob_service_client.get_container_client(self.container_drink_fee_name)
        self.semantic = False

        self.llm = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='test-1',
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            temperature=0.5,
            max_tokens=400
        )

        self.llm2 = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='test-1',
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            temperature=0.7,
            max_tokens=600
        )

        self.llm3 = AzureOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='test-1',
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            temperature=0.0,
            max_tokens=100,
            stop=['\n', '<|im_end|>', '<|im_sep|>']
        )

        self.retriever_public = SearchClient(
            endpoint=search_endpoint,
            index_name=public_index_name,
            credential=AzureKeyCredential(search_key),
            b=0.0,
            k1=0.3,
            searchMode="any"
        )

        self.default_search = SearchClient(
            endpoint=search_endpoint,
            index_name=semantic_index,
            credential=AzureKeyCredential(search_key),
            b=0.0,
            k1=0.3,
            searchMode="any"
        )

        self.retriever_drink = SearchClient(
            endpoint=search_endpoint,
            index_name=nois_drink_fee_index,
            credential=AzureKeyCredential(search_key),
            b=0.0,
            k1=0.3,
            searchMode="any"
        )

        self.retriever_policy = SearchClient(
            endpoint=search_endpoint,
            index_name=company_regulations_index,
            credential=AzureKeyCredential(search_key),
            b=0.0,
            k1=0.3,
            searchMode="any"
        )

        self.semantic_search = SearchClient(
            endpoint=search_endpoint,
            index_name=semantic_index,
            credential=AzureKeyCredential(search_key)
        )

        self.retriever_private = self.default_search

        self.qa_chain = load_qa_with_sources_chain(llm=self.llm, chain_type="stuff", prompt=PromptTemplate.from_template(self.chat_template))
        self.keyword_chain = LLMChain(llm=self.llm3, prompt=PromptTemplate.from_template(self.keyword_templ))
        self.classifier_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.classifier_template))
        self.drink_chain = load_qa_with_sources_chain(llm=self.llm2, chain_type="stuff", prompt=PromptTemplate.from_template(self.drink_fee_template))

    def get_document(self, query, retriever, n=3):
        # Get top 3 documents
        if not self.semantic or not self.private:
            res = retriever.search(search_text=query, top=n)

        else:
            temp = query.split(', ')
            q = temp[0]
            lang = 'en-US' if temp[1] == 'english' else 'vi-VN'

            res = retriever.search(
                search_text=q,
                query_type='semantic',
                query_language=lang,
                semantic_configuration_name="default",
                top=n,
            )

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

    def change_retriever(self):
        if not self.semantic:
            self.semantic = True
            self.retriever_private = self.semantic_search
            print("Using semantic search.")

        else:
            self.semantic = False
            self.retriever_private = self.default_search
            print("Using default search.")

    def get_history_as_txt(self, n=3):
        txt = ""
        hist = self.history_public

        if self.private:
            hist = self.history_private

        if len(hist) <= n:
            history = hist

        else:
            history = hist[len(hist) - n:]

        for i in history:
            txt += f"\n<|im_start|>user\n{i['user']}\n<|im_end|>\n"
            txt += f"<|im_start|>assistant\n{i['AI']}\n<|im_end|>"

        return txt

    def add_to_history(self, user_msg, ai_msg):
        hist = self.history_public
        if self.private:
            hist = self.history_private

        hist.append({'user': user_msg, 'AI': ai_msg})
        # print(hist)

    def chat(self, query):
        if self.private:
            return self.chat_private(query)

        return self.chat_public(query)

    def chat_public(self, query):
        keywords = self.keyword_chain({'question': query, 'context': self.get_history_as_txt()})['text']
        print(f"Full keywords: {keywords}")
        keywords = keywords.split(', ')[1]
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
        label = self.classifier_chain({'question': query, 'context': self.get_history_as_txt()})['text']
        print(f"Label: {label}")

        keywords = self.keyword_chain({'question': query, 'context': self.get_history_as_txt()})['text']
        print(f"Query: {query}\nKeywords: {keywords}")

        chain = self.qa_chain

        if label == "drink fee":
            # self.history_private = []

            # keyword_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.keyword_templ_drink_fee))
            # keywords_drink_fee = keyword_chain({'context': self.get_history_as_txt(), 'question': query})['text']
            # print(f"Drink fee keywords: {keywords_drink_fee}")

            doc = self.get_document(keywords, self.retriever_drink, 1)

            input_pandas = self.drink_chain({'input_documents': doc, 'question': query, 'context': self.get_history_as_txt()}, return_only_outputs=False)
            try:
                blob_name = doc[0].metadata['metadata_storage_name']
            except Exception as e:
                return {'output_text': f'Cannot generate response, error: {e}'}, None
        
            print(input_pandas['output_text'])
            temp_result = self.excel_drink_preprocess(input_pandas['output_text'], blob_name)
            # print(temp_result)
            result_doc = "Input: " + query +"\n Output: " + str(temp_result)
            print(result_doc)

            if """count""" not in input_pandas['output_text']:
                self.add_to_history(query, str(temp_result))
                return {'output_text': str(temp_result)}, doc
            doc[0].page_content = result_doc

        else:
            if self.semantic:
                lang = keywords.split(', ')[0].split(':')[1].lower()
                q = lang + ', ' + query
                print(f"Semantic search with query: {q}")

            else:
                q = keywords.split(', ')[1]

            doc = self.get_document(q, self.retriever_private)

        try:
            response = chain({'input_documents': doc, 'question': query, 'context': self.get_history_as_txt()},
                             return_only_outputs=False)
        except Exception as e:
            return {'output_text': f'Cannot generate response, error: {e}'}, doc

        self.add_to_history(query, response['output_text'])
        return response, doc

    def excel_drink_preprocess(self, input_pandas, file_name):
        sas_i = generate_blob_sas(
            account_name = account_name,
            container_name = self.container_drink_fee_name,
            blob_name = file_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1)
        )

        sas_url = 'https://' + account_name+'.blob.core.windows.net/' + self.container_drink_fee_name + '/' + file_name + '?' + sas_i

        df = pd.read_excel(sas_url, skiprows=1)
        df = df[df['FullName'].notnull()]
        df = df.iloc[:, df.columns.notna()]

        try:
            result_pandas = eval(input_pandas) 
        except Exception as e:
            return input_pandas

        return result_pandas

    def clear_history(self):
        self.history_public = []
        self.history_private = []
