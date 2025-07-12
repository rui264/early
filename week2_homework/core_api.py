# 核心的接口函数，fastAPI只需import core_api.py即可

from dotenv import load_dotenv
load_dotenv()
from memory_manager import RedisConversationMemory
from agent_executor import create_controller_agent
from llm_factory import get_llm

def multi_agent_ask(session_id: str, question: str, provider: str = "openai", model: str = "gpt-4-turbo") -> str:
    """
    多代理问答主入口
    :param session_id: 会话ID
    :param question: 用户问题
    :param provider: 大模型提供商（如 'openai', 'qwen'）
    :param model: 大模型名称（如 'gpt-3.5-turbo', 'gpt-4-turbo', 'qwen-turbo'）
    :return: AI回复内容
    """
    memory = RedisConversationMemory(session_id)
    llm = get_llm(provider, model)
    controller = create_controller_agent(llm)
    # 获取历史
    chat_history = []
    for msg in memory.get_history():
        if getattr(msg, 'type', None) == "human":
            chat_history.append({"role": "user", "content": msg.content})
        elif getattr(msg, 'type', None) == "ai":
            chat_history.append({"role": "assistant", "content": msg.content})
    agent_input = {
        "input": question,
        "chat_history": chat_history
    }
    result = controller.invoke(agent_input)
    # 存历史
    memory.add_user_message(question)
    memory.add_ai_message(result['output'])
    return result['output']

def upload_knowledge_file(session_id: str, file_path: str) -> str:
    from agents.agent_fileqa import FileQASystem, get_fileqa_tool
    file_qa_cache = {}
    file_qa_cache[(file_path, )] = FileQASystem(file_path)
    return f"知识库已更新: {file_path}"

def get_chat_history(session_id: str) -> list:
    """
    获取某个会话的历史记录
    :param session_id: 会话ID
    :return: 历史消息列表 [{"role": "user"/"assistant", "content": "..."}]
    """
    memory = RedisConversationMemory(session_id)
    history = []
    for msg in memory.get_history():
        if getattr(msg, 'type', None) == "human":
            history.append({"role": "user", "content": msg.content})
        elif getattr(msg, 'type', None) == "ai":
            history.append({"role": "assistant", "content": msg.content})
    return history

# get_chat_history 返回的是一个列表，每个元素是一个字典，格式如下：
"""
[
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好，有什么可以帮您？"},
    {"role": "user", "content": "帮我总结一下xxx.pdf"},
    {"role": "assistant", "content": "文件主要内容如下..."},
    # ...
]
"""