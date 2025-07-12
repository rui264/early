# 测试对话函数的功能
from core_api import multi_agent_ask, delete_chat_history

session_id = "560"
question = "今天晚上吃什么？"
provider = "openai"  # 或 "qwen"
model = "gpt-4-turbo"  # 或 "qwen-turbo"

# answer = multi_agent_ask(session_id, question, provider, model)
# print("AI回复：", answer)

# delete_chat_history(session_id)