from langchain.prompts import PromptTemplate
from langchain.document_transformers import Document
from azure.core.credentials import AzureKeyCredential
from langchain.chains import LLMChain
from azure.search.documents import SearchClient
from langchain.chat_models import AzureChatOpenAI
from langchain.chains.qa_with_sources import load_qa_with_sources_chain

public_index_name = "nois-public-v3-index"
private_index_name = "nois-private-v3-index"
company_regulations_index = "nois-company-regulations-v2"
nois_drink_fee_index = "nois-drink-fee-index"
search_endpoint = 'https://search-service01.search.windows.net'
search_key = '73Swa5YqUR5IRMwUIqOH6ww2YBm3SveLv7rDmZVXtIAzSeBjEQe9'

# os.environ["AZURE_COGNITIVE_SEARCH_SERVICE_NAME"] = "search-service01"
# os.environ["AZURE_COGNITIVE_SEARCH_API_KEY"] = "73Swa5YqUR5IRMwUIqOH6ww2YBm3SveLv7rDmZVXtIAzSeBjEQe9


class chatAI:
    keyword_templ = """<|im_start|>system
Below is a history of the conversation so far, and an input question asked by the user that needs to be answered by querying relevant company documents.
Generate a search query based on the conversation and the new question. Use Roman numerals for chapter numbers. Only include the most important queries.
Replace AND with + and OR with |. Do not answer the question.

Chat history:{context}

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
Input: Điều 7 chương 2 gồm nội dung gì?
Output: ("điều 7" + "chương II") | ("article 7" + "chapter II")
<|im_end|>

Input: {question}
<|im_start|>assistant
Output:"""

    chat_template = """<|im_start|>system
Assistant helps the company employees and users with their questions about the companies New Ocean and NOIS. Your answer must adhere to the following criteria:
- Be brief in your answers. You may use the provided sources to help answer the question. If there isn't enough information, say you don't know. If asking a clarifying question to the user would help, ask the question.
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

    classifier_template = """<|im_start|>system
Given a sentence, assistant will determine if the sentence belongs in 1 of 3 categories, which are:
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
<|im_end|>

Input: {question}
<|im_start|>assistant
Output:"""

    drink_fee_template = """<|im_start|>system

Sources:
{summaries}

You must follow this rule:
1. If the input is Vietnamese, you must answer in Vietnamese.  If the input is  English, the output is English.
2. If user ask to list about people who paid the water money or not paid, you must list all like require of user.
If the user asks any questions not related to New Ocean or NOIS, apologize and request another question from the user. If the user greets you, respond accordingly.
If given a question with both languages present, ask the user which language they prefer.
3. Form of list should have a endline.
For example: 
1. hung.bui@nois.vn BÙI TUẤN HƯNG 68000 'newline'
2. hiep.dang@nois.vn ĐẶNG DUY HIỆP 33542 33542 Done 'newline'
3. tai.dang@nois.vn ĐẶNG HỮU TÀI 56100 56100 Done 'newline'

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

        self.llm = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='test-1',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.5,
            max_tokens=400
        )

        self.llm2 = AzureChatOpenAI(
            openai_api_type="azure",
            openai_api_base='https://openai-nois-intern.openai.azure.com/',
            openai_api_version="2023-03-15-preview",
            deployment_name='test-1',
            openai_api_key='400568d9a16740b88aff437480544a39',
            temperature=0.0,
            max_tokens=600
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

        self.qa_chain = load_qa_with_sources_chain(llm=self.llm, chain_type="stuff", prompt=PromptTemplate.from_template(self.chat_template))
        self.keywordChain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.keyword_templ))
        self.classifier_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.classifier_template))
        self.drink_chain = load_qa_with_sources_chain(llm=self.llm2, chain_type="stuff", prompt=PromptTemplate.from_template(self.drink_fee_template))

    def get_document(self, query, retriever):
        # Get top 4 documents
        res = retriever.search(search_text=query, top=3)

        doc_num = 1
        doc = []
        for i in res:
            newdoc = Document(page_content=i['content'],
                              metadata={'@search.score': i['@search.score'], 'source': f'doc-{doc_num}'})

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
        keywords = self.keywordChain({'question': query, 'context': self.get_history_as_txt()})['text']
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
        label = self.classifier_chain(query)['text']

        keywords = self.keywordChain({'question': query, 'context': self.get_history_as_txt()})['text']
        print(f"Query: {query}\nKeywords: {keywords}")

        chain = self.qa_chain

        if label == "drink fee":
            doc = self.get_document(keywords, self.retriever_drink)

        elif label == "policy":
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

    def excel_drink_preprocess(self, doc):
        doc = doc[:1]

        done_lines = []
        done_name = []
        not_done_lines = []
        not_done_name = []

        for x in doc:
            count_done = x.page_content.count("Done")
            print(count_done)
            print(x.page_content)
            lines = x.page_content.split('\n')

            # Create empty lists to store the line numbers with and without "Done"

            # Loop through the lines and check for "Done"
            for line in lines:
                if "Done" in line:
                    # If "Done" is found, extract the line number and fullname, and add it to the done list
                    fields = line.split()
                    number = fields[0]
                    fullname = ' '.join(fields[2:-3])
                    done_name.append(fullname)
                    done_lines.append(number)
                elif line.startswith('\t'):
                    # If the line starts with a tab character, it's a data row
                    fields = line.split()
                    number = fields[0]
                    fullname = ' '.join(fields[2:-2])
                    not_done_name.append(fullname)
                    not_done_lines.append(number)

            # Print the lists of line numbers that have and do not have "Done"
            print("Lines with 'Done':", done_lines)
            print(done_name)
            print("Lines without 'Done':", not_done_lines[2:-4])
            print(not_done_name[2:-4])
            total_people = len(done_lines) + len(not_done_lines[2:-4])
            print(total_people)

            final_hidden_prompt = "Có tổng cộng" + str(total_people) + "người đã mua nước. Trong đó có" + str(
                len(done_name)) + "người đã đóng tiền nước, bao gồm:" + str(done_name) + "\n" + str(
                len(not_done_name[2:-4])) + "người chưa đóng tiền nước, bao gồm" + str(not_done_name[2:-4])
            print(final_hidden_prompt)
            x.page_content = final_hidden_prompt + x.page_content

        return doc

    def clear_history(self):
        self.history_public = []
        self.history_private = []
