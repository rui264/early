# 命令行测试文件

from dotenv import load_dotenv
load_dotenv()
from memory_manager import RedisConversationMemory
from agent_executor import create_controller_agent
from llm_factory import get_llm

# 文件上传与知识库更新
from agents.agent_fileqa import FileQASystem, get_fileqa_tool

def main():
    session_id = input("请输入会话ID(用于区分多用户): ") or "multi_agent_auto_coop"
    memory = RedisConversationMemory(session_id)
    provider = input("请输入大模型类型(openai/qwen，默认openai): ") or "openai"
    model = input("请输入模型名(如gpt-4-turbo/qwen-turbo，默认gpt-4-turbo): ") or "gpt-4-turbo"
    memory = RedisConversationMemory(session_id)
    llm = get_llm(provider, model)
    controller = create_controller_agent(llm)
    print("多代理协作系统 (输入 'exit' 结束, 输入 'upload <文件路径>' 上传知识库)")
    chat_history = []
    while True:
        user_input = input("请输入问题：")
        if user_input == "exit":
            break
        if user_input.startswith("upload "):
            file_path = user_input.split(" ", 1)[1]
            try:
                file_qa_cache = {}
                file_qa_cache[(file_path,)] = FileQASystem(file_path)
                print(f"知识库已更新: {file_path}")
            except Exception as e:
                print(f"知识库上传失败: {e}")
            continue
        # 组装输入
        agent_input = {
            "input": user_input,
            "chat_history": chat_history
        }
        result = controller.invoke(agent_input)
        print(f"【最终回复】: {result['output']}")
        # 更新历史
        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "assistant", "content": result['output']})
        # 写入Redis
        memory.add_user_message(user_input)
        memory.add_ai_message(result['output'])

if __name__ == "__main__":
    main()