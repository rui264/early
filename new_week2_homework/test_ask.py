# 测试对话函数的功能
from core_api import multi_agent_ask, delete_chat_history

session_id = "560"
# question = r"upload D:\test.pdf"
question="介绍一下你自己"
provider = "spark"
model = "generalv3"

answer = multi_agent_ask(session_id, question, provider, model)
print("AI回复：", answer)

# delete_chat_history(session_id)