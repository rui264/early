# 测试获取会话历史记录的功能
# get_chat_history 返回的是一个列表，每个元素是一个字典

from core_api import get_chat_history

session_id = "abc"  # 这里填你实际的会话ID
history = get_chat_history(session_id)

for msg in history:
    # print(f"{msg['role']}: {msg['content']}")
    print(msg)