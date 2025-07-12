from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from agents.agent_math import get_math_tool
from agents.agent_search import get_search_tool
from agents.agent_knowledge import get_knowledge_tool
from agents.agent_fileqa import get_fileqa_tool

def create_controller_agent(llm):
    math_tool = get_math_tool(llm)
    search_tool = get_search_tool(llm)
    knowledge_tool = get_knowledge_tool(llm)
    fileqa_tool = get_fileqa_tool(llm)
    TOOLS = [math_tool, search_tool, knowledge_tool, fileqa_tool]
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个高级AI助手，可以访问多种工具解决复杂问题。"),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    agent = create_openai_tools_agent(llm, TOOLS, prompt)
    return AgentExecutor(agent=agent, tools=TOOLS, verbose=True)