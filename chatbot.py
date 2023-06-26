from langchain.prompts import PromptTemplate
from langchain.document_transformers import Document
from azure.core.credentials import AzureKeyCredential
from langchain.chains import LLMChain
from azure.search.documents import SearchClient
from langchain.chat_models import AzureChatOpenAI
from langchain.chains.qa_with_sources import load_qa_with_sources_chain

public_index_name = "nois-public-data-index"
private_index_name = "nois-private-data-index"
company_regulations_index = "company-regulations-index"
nois_drink_fee_index = "nois-drink-fee-index"
search_endpoint = 'https://search-service01.search.windows.net'
search_key = '73Swa5YqUR5IRMwUIqOH6ww2YBm3SveLv7rDmZVXtIAzSeBjEQe9'

# os.environ["AZURE_COGNITIVE_SEARCH_SERVICE_NAME"] = "search-service01"
# os.environ["AZURE_COGNITIVE_SEARCH_API_KEY"] = "73Swa5YqUR5IRMwUIqOH6ww2YBm3SveLv7rDmZVXtIAzSeBjEQe9"


class chatAI:
    keyword_templ = """<|im_start|>system
Given a sentence and a conversation about the companies New Ocean Automation System and NOIS, assistant will extract keywords based on the conversation and the sentence and translate them to Vietnamese if they're in English and vice versa.
Your output will be on one line, in both languages if possible and separated by commas. Do not duplicate keywords.
Assume the context is about the companies unless specified otherwise. Only return the keywords, do not output anything else. Do not answer the questions, just return the keywords.
Reuse the most recent keywords and do not create new keywords if the sentence has continuity.
EXAMPLE
Input: Ai chưa đóng tiền nước tháng 5?
Output: tiền nước tháng 05, May drink fee
Input: Was Pepsico a customer of New Ocean?
Output: Pepsico
Input: What is FASF?
Output: FASF
Input: What is chapter 1, article 4 of the company's policy about?
Output: chapter I article 4, chương I điều 4, company's policy, quy định công ty
Input: Chương 2, điều 7 gồm nội dung gì?
Ouput: chương II điều 7, chapter II article 7
<|im_end|>
{context}
<|im_start|>user
Input: {question}
<|im_end|>
<|im_start|>assistant
Output:"""

    chat_template = """<|im_start|>system
You must follow this rule:
1. If the input is Vietnamese, you must answer in Vietnamese.  If the input is  English, the output is English.
2. Assistant helps the company employees and users with their questions about the companies New Ocean Automation System and NOIS. Your answer must adhere to the following criteria:
- Be brief in your answers. Answer ONLY with the facts listed in the list of sources below. If there isn't enough information below, say you don't know. Do not generate answers that don't use the sources below. If asking a clarifying question to the user would help, ask the question.
- If the user asks any questions not related to New Ocean Automation System or NOIS, apologize and request another question from the user. If the user greets you, respond accordingly.

Sources:
{summaries}
<|im_end|>
{context}
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

    policy_template = """<|im_start|>system

Sources:
{summaries}

You must follow this rule:
1. If the input is Vietnamese, you must answer in Vietnamese.  If the input is  English, the output is English.
2. Because this is Company regulations, you must answer same as in document except you are required to paraphraise.
3. Company regulations includes 10 chapters and 36 articles from 1 to 36:
CHAPTER I has 4 articles from article 1 to article 4,
CHAPTER II has 8 articles from article 5 to 13,
CHAPTER III has 6 articles from article 14 to 19,
CHAPTER IV has 2 articles from article 20 to 21,
CHAPTER V has 2 articles from article 22 to 23,
CHAPTER VI has 2 articles from article 24 to 25,
CHAPTER VII has 2 articles from article 26 to 27,
CHAPTER VIII has 7 articles from article 28 to 34,
CHAPTER IX has 1 articles,
CHAPTER X has 1 articles
If user just ask about article, you just answer the chapter that article belongs to.
for example: if input is "article 14" , so the output is "article 14 in chapter III". After ask user whether user want ask detailly about that article.
4. You must read Roman numerals: I~1,II~2,III~3, IV~4,V~5,VI~6,VII~7,VIII~8,IX~9,X~10
For example: Chapter V means Chapter 5 and reverse
5. Assistant is a friendly chatbot that helps the company employees and users with their questions about the companies New Ocean and NOIS in their language. Be brief in your answers.
Answer ONLY with the facts listed in the list of sources below. If there isn't enough information below, say you don't know. Do not generate answers that don't use the sources below. If asking a clarifying question to the user would help, ask the question.
If the user asks any questions not related to New Ocean or NOIS, apologize and request another question from the user. If the user greets you, respond accordingly.
If given a question with both languages present, ask the user which language they prefer.

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
            temperature=0,
            max_tokens=600
        )

        self.retriever_public = SearchClient(
            endpoint=search_endpoint,
            index_name=public_index_name,
            credential=AzureKeyCredential(search_key)
        )

        self.retriever_private = SearchClient(
            endpoint=search_endpoint,
            index_name=private_index_name,
            credential=AzureKeyCredential(search_key)
        )

        self.retriever_policy = SearchClient(
            endpoint=search_endpoint,
            index_name=company_regulations_index,
            credential=AzureKeyCredential(search_key)
        )

        self.retriever_drink = SearchClient(
            endpoint=search_endpoint,
            index_name=nois_drink_fee_index,
            credential=AzureKeyCredential(search_key)
        )

        self.qa_chain = load_qa_with_sources_chain(llm=self.llm, chain_type="stuff", prompt=PromptTemplate.from_template(self.chat_template))
        self.keywordChain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.keyword_templ))
        self.classifier_chain = LLMChain(llm=self.llm2, prompt=PromptTemplate.from_template(self.classifier_template))
        self.policy_chain = load_qa_with_sources_chain(llm=self.llm2, chain_type="stuff", prompt=PromptTemplate.from_template(self.policy_template))
        self.drink_chain = load_qa_with_sources_chain(llm=self.llm2, chain_type="stuff", prompt=PromptTemplate.from_template(self.drink_fee_template))

    def get_document(self, query, retriever):
        # Get top 4 documents
        res = retriever.search(search_text=query, top=4)

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

        for i in hist:
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
        doc = self.get_document(keywords, self.retriever_public)

        response = self.qa_chain({'input_documents': doc, 'question': query, 'context': self.get_history_as_txt()}, return_only_outputs=False)
        self.add_to_history(query, response['output_text'])
        return response, doc

    def chat_private(self, query):
        label = self.classifier_chain(query)['text']

        keywords = self.keywordChain({'question': query, 'context': self.get_history_as_txt()})['text']
        print(f"Query: {query}\nKeywords: {keywords}")

        chain = self.qa_chain
        doc = self.get_document(keywords, self.retriever_private)

        if label == "drink fee":
            doc = self.get_document(keywords, self.retriever_drink)
            chain = self.drink_chain
            doc = self.excel_drink_preprocess(doc)

        elif label == "policy":
            chain = self.policy_chain
            doc = self.get_document(keywords, self.retriever_policy)

        response = chain({'input_documents': doc, 'question': query, 'context': self.get_history_as_txt()},
                         return_only_outputs=False)

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
