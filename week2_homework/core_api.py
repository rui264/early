# 核心的接口函数，fastAPI只需import core_api.py即可

from dotenv import load_dotenv
load_dotenv()
from memory_manager import RedisConversationMemory
import redis
import os
import time

def multi_agent_ask(session_id: str, question: str, provider: str = "openai", model: str = "gpt-4-turbo") -> dict:
    """
    多代理问答主入口，返回AI回复和提问时间
    """
    # 自动补全文件路径：如果问题里没有|，自动加上session记忆的文件路径
    if "|" not in question:
        r = redis.Redis.from_url(os.environ.get("REDIS_URL"))
        file_key = f"session_files:{session_id}"
        files = r.smembers(file_key)
        if files:
            file_path = list(files)[-1].decode()  # 取最新上传的文件
            question = f"{file_path}|{question}"
    from langgraph_multi_agent import TrueMultiAgentSystem
    multi_agent = TrueMultiAgentSystem(session_id, provider, model)
    result = multi_agent.ask(question)
    # 记录时间戳
    r = redis.Redis.from_url(os.environ.get("REDIS_URL"))
    time_key = f"chat_message_time:{session_id}"
    history_len = r.hlen(time_key)
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    r.hset(time_key, history_len, now)
    return {"answer": result, "question_time": now}

def upload_knowledge_file(session_id: str, file_path: str) -> str:
    from langgraph_multi_agent import TrueMultiAgentSystem
    multi_agent = TrueMultiAgentSystem(session_id, "openai", "gpt-4-turbo")
    result = multi_agent.upload_file(file_path)
    # 记忆文件路径到session
    r = redis.Redis.from_url(os.environ.get("REDIS_URL"))
    file_key = f"session_files:{session_id}"
    r.sadd(file_key, file_path)
    return result


# 一次问答会显示一个时间戳（问问题的时间）session_id
"""
格式如下：
{'role': 'user', 'content': '介绍一下你自己', 'time': '2025-07-12 15:37:53'}
{'role': 'assistant', 'content': '我是一个知识库专家，负责回答基于历史对话和知识库的问题。通过分析大量数据，我能提供准确的答案和解释，帮助用户理解复杂信息，并解决各领域的具体疑问。无论是历史、科技、文化等问题，我都能提供专业的解答和支持。', 'time': ''}
前端可以将时间也显示出来，方便用户查看历史消息的时间。
"""
def get_chat_history(session_id: str) -> list:
    """
    获取某个会话的历史记录，带时间戳
    :param session_id: 会话ID
    :return: 历史消息列表 [{"role": "user"/"assistant", "content": "...", "time": "..."}]
    """
    memory = RedisConversationMemory(session_id)
    history = []
    r = redis.Redis.from_url(os.environ.get("REDIS_URL"))
    time_key = f"chat_message_time:{session_id}"
    time_map = r.hgetall(time_key)
    # 按顺序为每条消息加上时间戳
    for idx, msg in enumerate(memory.get_history()):
        msg_time = time_map.get(str(idx).encode(), b"").decode() if str(idx).encode() in time_map else ""
        if getattr(msg, 'type', None) == "human":
            history.append({"role": "user", "content": msg.content, "time": msg_time})
        elif getattr(msg, 'type', None) == "ai":
            history.append({"role": "assistant", "content": msg.content, "time": msg_time})
    return history

# 删除指定会话的全部历史记录
def delete_chat_history(session_id: str) -> bool:
    memory = RedisConversationMemory(session_id)
    memory.clear()
    # 同时清理时间戳
    r = redis.Redis.from_url(os.environ.get("REDIS_URL"))
    time_key = f"chat_message_time:{session_id}"
    r.delete(time_key)
    return True


# 重命名会话(改session_id)
def rename_session_id(old_session_id: str, new_session_id: str) -> bool:
    old_memory = RedisConversationMemory(old_session_id)
    new_memory = RedisConversationMemory(new_session_id)
    history = old_memory.get_history()
    new_memory.clear()
    # 迁移消息内容
    for msg in history:
        if getattr(msg, 'type', None) == "human":
            new_memory.add_user_message(msg.content)
        elif getattr(msg, 'type', None) == "ai":
            new_memory.add_ai_message(msg.content)
    old_memory.clear()
    # 迁移时间戳
    r = redis.Redis.from_url(os.environ.get("REDIS_URL"))
    old_time_key = f"chat_message_time:{old_session_id}"
    new_time_key = f"chat_message_time:{new_session_id}"
    if r.exists(old_time_key):
        time_map = r.hgetall(old_time_key)
        if time_map:
            r.delete(new_time_key)
            r.hmset(new_time_key, time_map)
        r.delete(old_time_key)
    return True

# 获取所有的会话ID（还没写好）
# def get_all_session_ids() -> list:
#     r = redis.Redis.from_url(os.environ.get("REDIS_URL"))
#     keys = r.keys("chat_message_history:*")
#     session_ids = [k.decode().split(":")[-1] for k in keys]
#     return session_ids


