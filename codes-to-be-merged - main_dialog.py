elif command.lower() == "agent":
await step_context.context.send_activity(
    self.bot.toggle_agent(me_info['mail'])
)

elif me_info['mail'] in self.bot.agent_session and self.bot.agent_session[me_info['mail']][0] and \
     not self.bot.agent_session[me_info['mail']][1]:
msg = step_context.values["command"]
agent_arg = 1
agent_type = self.bot.choose_agent(msg).strip()

if agent_type == "subdel":
    agent_arg = 2

t1 = threading.Thread(target=run_agent, args=(self, msg, me_info['mail'], agent_arg,), daemon=True)
t1.start()

new_msg = get_bot_response(self, me_info['mail'])

await step_context.context.send_activity(
    new_msg
)

elif me_info['mail'] in self.bot.agent_session and self.bot.agent_session[me_info['mail']][1]:
msg = step_context.values['command']
print(f"Still in agent session, current user message: {msg}")
self.bot.agent[me_info['mail']].msg.input = msg

new_msg = get_bot_response(self, me_info['mail'])

await step_context.context.send_activity(
    new_msg
)

def run_agent(obj: MainDialog, query, email, agent_type):
    obj.bot.agent_session[email][1] = True
    if agent_type == 1:
        print("Running agent 1...")
        obj.bot.agent[email].run1(query)

    else:
        print("Running agent 2...")
        obj.bot.agent[email].run2(query)

    obj.bot.agent_session[email][1] = False
    return


def get_bot_response(obj: MainDialog, email):
    while not obj.bot.agent[email].msg.output:
        pass

    msg = obj.bot.agent[email].msg.output
    obj.bot.agent[email].msg.reset()

    return msg