from langchain.prompts import PromptTemplate
from langchain.document_transformers import Document
from azure.core.credentials import AzureKeyCredential
from langchain.chains import LLMChain
from azure.search.documents import SearchClient
from langchain.chat_models import AzureChatOpenAI
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta

import re

# image processing
from PIL import Image
import urllib.request
import io

fasf_text_index = "fasf-text-01-index"
fasf_images_index = "fasf-images-index" 

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
Do not answer the question. Output queries must be in Vietnamese.
Examples are provided down below:

EXAMPLES
Input: Ai là giám đốc điều hành của NOIS?
Ouput: giám đốc điều hành 
Input: Số người chưa đóng tiền nước tháng 5?
Output: tiền nước tháng 05 chưa đóng 
Input: Ai đã đóng tiền nước tháng 4?
Output: tiền nước tháng 04 đã đóng 
Input: Danh sách người đóng tiền nước tháng 3?
Output: tiền nước tháng 03
Input: Was Pepsico a customer of New Ocean?

Chat history:{context}

Question:
{question}

Search query:
"""

    chat_template = """<|im_start|>system
Assistant helps the company employees and users with their questions about the companies New Ocean and NOIS. Your answer must adhere to the following criteria:
You must follow this rule:
- If question is in English, answer in English. If question is in Vietnamese, answer in Vietnamese 
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

    fasf_template = """<|im_start|>system
- The output must be in Vietnamese
- All strings that start with "<" and end with ">" MUST be in the output, in the same position in the original document.
- Be brief but friendly in your outputs. You may use the provided sources to help output the question. 
- If there isn't enough information, say you don't know. If asking a clarifying question to the user would help, ask the question.
- If the user greets you, respond accordingly.
- If you have to list step of a process, you MUST output with "Bước" before number of step
For example: Bước 1:...
             Bước 2:...

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

    classifier_fasf = """<|im_start|>system
Given a sentence, assistant will determine if the sentence belongs in 1 of 2 categories, which are:
- yes
- no
You answer the question "Is the user's question related to FASF?"
EXAMPLE:
Input: các bước cập nhật thông tin user
Output: yes
Input: quy trình cập nhật thông tin user
Output: yes
Input: cách để Tìm kiếm máy sản xuất?
Output: yes
Input: cách để sao để tôi chép phiếu nhập liệu
Output: yes
Inout: làm sao để Tìm kiếm phiếu cần nhập?
Output: yes
Input: tổng thống Mỹ là ai
Output: no
Input: công ty có những ngày lễ nào
Output: no
Input: tổng tiền nước tháng này là bao nhuêu
Output: no
<|im_end|>

Input: {question}
<|im_start|>assistant
Output:"""

    def __init__(self):
        self.history_fasf = []
        self.user = {"username":' ', "mail":' '}

        self.llm = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='gpt-35-turbo-16k',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.5,
            max_tokens=2000
        )

        self.llm2 = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='gpt-35-turbo-16k',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.7,
            max_tokens=600
        )

        self.llm3 = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='gpt-35-turbo-16k',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.0,
            max_tokens=600
        )

        self.retriever_text_fasf = SearchClient(
            endpoint=search_endpoint,
            index_name=fasf_text_index,
            credential=AzureKeyCredential(search_key),
            b=1.0,
            k1=3.0,
            searchMode="all"
        )


        self.qa_chain = load_qa_with_sources_chain(llm=self.llm, chain_type="stuff", prompt=PromptTemplate.from_template(self.chat_template))
        self.keywordChain = LLMChain(llm=self.llm3, prompt=PromptTemplate.from_template(self.keyword_templ))
        
        self.fasf_classifier_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.classifier_fasf))
        self.fasf_chain = load_qa_with_sources_chain(llm=self.llm, chain_type="stuff", prompt=PromptTemplate.from_template(self.fasf_template))
        # self.text_fasf_chain = load_qa_with_sources_chain(llm=self.llm2, chain_type="stuff", prompt=PromptTemplate.from_template(self.drink_fee_template))

    def get_document(self, query, retriever):
        # Get top 4 documents
        lang = 'vi-VN'
        res = retriever.search(
                search_text=query,
                query_type='semantic',
                query_language=lang,
                semantic_configuration_name="default",
                top=1,
            )

        doc_num = 0
        doc = []
        for i in res:
            newdoc = Document(page_content=i['content'],
                              metadata={'@search.score': i['@search.score'],
                                        'metadata_storage_name': i['metadata_storage_name'], 'source': f'doc-{doc_num}'})

            doc.append(newdoc)
            doc_num += 1

        return doc

    def get_history_as_txt(self, n=3):
        txt = ""
        hist = self.history_fasf

        if len(hist) <= n:
            history = hist

        else:
            history = hist[len(hist) - n:]

        for i in history:
            txt += f"\n<|im_start|>user\n{i['user']}\n<|im_end|>\n"
            txt += f"<|im_start|>assistant\n{i['AI']}\n<|im_end|>"

        return txt

    def add_to_history(self, user_msg, ai_msg):
        hist = self.history_fasf

        hist.append({'user': user_msg, 'AI': ai_msg})

    def chat(self, query):
        return self.chat_fasf(query)
    
    def chat_fasf(self, query):
        label = self.fasf_classifier_chain(query)['text']
        # keywords = self.keywordChain({'question': query, 'context': self.get_history_as_txt()})['text']
        chain = self.fasf_chain
        doc = self.get_document(query, self.retriever_text_fasf)
        print(doc)
        print(label)
        response = """"""
        try:
            if label == "yes":
                images = re.findall(r'<.*?>',  doc[0].page_content)
                for line in doc[0].page_content.split('\n'):
                    
                    if any(search_string in line for search_string in images):
                        filename = line[line.index('<')+1:line.index('>')] + ".png"
                        link_image = self.get_image(filename, "fasf-images")

                        with urllib.request.urlopen(link_image) as url:
                            f = io.BytesIO(url.read())

                        img = Image.open(f)

                        # Get the size of the image
                        w, h = img.size

                        # if wanted to adjust the sized wanted to limit change here
                        if w > 500 and h >500:
                            w /= 2
                            h /= 2

                        response += f"""<img src="{link_image}" alt="Example Image" style="width: {w}px; height: {h}px; border: 3px solid yellow; margin-top: 5px;
                    margin-bottom: 5px;">"""
                    else:
                        response += '<div>' + line + '</div>'
            else:
                temp_response = chain({'input_documents': doc, 'question': query, 'context': self.get_history_as_txt(),
                                'user_info': ''}, return_only_outputs=False) 
                response += '<div>' + temp_response['output_text'] + '</div>'
        except Exception as e:
            return {'output_text': f'Cannot generate response, error: {e}'}, doc

        self.add_to_history(query, response)         
        return response
    
    def get_image(self, blob_name, container_name):
        sas_i = generate_blob_sas(account_name = account_name,
                            container_name = container_name,
                            blob_name = blob_name,
                            account_key=account_key,
                            permission=BlobSasPermissions(read=True),
                            expiry=datetime.utcnow() + timedelta(hours=1))
        sas_url = 'https://' + account_name+'.blob.core.windows.net/' + container_name + '/' + blob_name + '?' + sas_i
        
        return sas_url

    def clear_history(self):
        self.history_fasf = []