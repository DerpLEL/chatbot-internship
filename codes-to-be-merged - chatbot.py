choose_agent_prompt = '''<|im_start|>system
Given a request/question, classify whether or not the given request/question belongs to one of these 2 classes:
- info
- subdel
DO NOT answer the question/fulfill the request. Only classification is required.

EXAMPLE
Input: I want to submit a leave application.
Output: subdel
Input: I want to delete a leave application.
Output: subdel
Input: How many day-offs do I have left?
Output: info
Input: What is my job title?
Output: info

<|im_end|>

<|im_start|>user
Input: {question}
<|im_end|>
<|im_start|>assistant
Output: '''

self.agent = {}
self.agent_session = {}

self.classifier_agent_type = LLMChain(llm=self.llm3,
                                              prompt=PromptTemplate.from_template(self.choose_agent_prompt))


def toggle_agent(self, email):
    if email not in self.agent_session:
        self.agent[email] = Agent(email)
        self.agent_session[email] = [True, False]
        return f"Agent has been enabled for user {email}"

    if not self.agent_session[email][0]:
        self.agent_session[email][0] = True
        return f"Agent has been enabled for user {email}"

    self.agent_session[email][0] = False
    return f"Agent has been disabled for user {email}"

def choose_agent(self, query):
    return self.classifier_agent_type(query)['text']