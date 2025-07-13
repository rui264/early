#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真正的多代理协作系统
支持多个Agent并行处理和协作
"""

import os
import asyncio
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.runnables import RunnableLambda
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 导入现有的组件
from agents.agent_math import get_math_tool
from agents.agent_search import get_search_tool
from agents.agent_knowledge import get_knowledge_tool
from agents.agent_fileqa import get_fileqa_tool
from llm_factory import get_llm
from memory_manager import RedisConversationMemory

load_dotenv()

# 定义状态类型
from typing import TypedDict, Annotated

os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

class MultiAgentState(TypedDict):
    user_input: Annotated[str, "用户输入"]
    chat_history: Annotated[List[BaseMessage], "对话历史"]
    agent_results: Annotated[Dict[str, str], "各个Agent的结果"]
    agent_analysis: Annotated[Dict[str, str], "各个Agent的分析"]
    collaboration_plan: Annotated[str, "协作计划"]
    final_answer: Annotated[str, "最终答案"]
    next_agents: Annotated[List[str], "下一步要执行的Agent"]

class TrueMultiAgentSystem:
    """真正的多代理协作系统"""
    
    def __init__(self, session_id: str, provider: str = "openai", model: str = "gpt-4-turbo"):
        self.session_id = session_id
        self.memory = RedisConversationMemory(session_id)
        self.llm = get_llm(provider, model)
        self.file_qa_cache = {}
        
        # 创建各个Agent的工具
        self.math_tool = get_math_tool(self.llm)
        self.search_tool = get_search_tool(self.llm)
        self.knowledge_tool = get_knowledge_tool(self.llm)
        self.fileqa_tool = get_fileqa_tool(self.llm)
        
        # 创建各个Agent
        self.agents = self._create_agents()
        
        # 创建LangGraph工作流
        self.workflow = self._create_workflow()

    
    def _create_agents(self) -> Dict[str, AgentExecutor]:
        """创建各个专业Agent"""
        agents = {}
        
        # 通用对话Agent
        general_prompt = ChatPromptTemplate.from_messages([
            ("system", 
"""你是一个通用对话助手，专注于与用户进行日常闲聊、常见问答和一般性问题的解答。你的任务是：
1. 用自然、亲切、简洁的语言回复用户。
2. 回答要有温度，避免机械式回复。
3. 只处理日常对话、闲聊、简单问候等问题，遇到专业领域问题请建议用户提更具体的问题。

【示例】
用户：你好！
你：你好呀！很高兴见到你，有什么可以帮您的吗？
用户：讲个笑话
你：好的！为什么数学书总是很难过？因为它有太多的问题！
"""),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])
        general_agent = create_openai_tools_agent(self.llm, [], general_prompt)
        agents["general"] = AgentExecutor(agent=general_agent, tools=[], verbose=True)
        
        # 数学Agent
        math_prompt = ChatPromptTemplate.from_messages([
            ("system", 
"""你是顶级数学专家，专注于数学计算、推理和公式推导。你的任务是：
1. 对于用户的数学问题，给出详细的计算步骤和最终答案。
2. 如果问题包含非数学部分，请将相关部分交由其他agent处理，不要直接拒绝。
3. 回答要简明、准确，必要时分点说明。
4. 只处理与数学相关的问题，不要编造与数学无关的内容。

【示例】
用户：2的100次方是多少？
你：步骤1：2^10=1024，2^20=1048576，2^100=1267650600228229401496703205376
最终答案：2的100次方是1267650600228229401496703205376
用户：请查一下今天北京的最高气温，并计算比昨天高了多少度，如果昨天是28度。
你：本问题需要与search agent协作，search agent负责查找今天北京的最高气温，我将根据其结果进行温度差计算。
"""),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])
        math_agent = create_openai_tools_agent(self.llm, [self.math_tool], math_prompt)
        agents["math"] = AgentExecutor(agent=math_agent, tools=[self.math_tool], verbose=True)


        # 搜索Agent
        search_prompt = ChatPromptTemplate.from_messages([
            ("system", 
"""你是权威信息检索专家，专注于为用户查找最新、最权威的实时信息。你的任务是：
1. 必须主动使用互联网工具（如search工具）快速定位，查找并返回用户需要的最新权威信息，不要让用户自己去查。
2. 回答时要简明扼要，直接给出结论，并注明信息来源（如网站名、数据出处）。
3. 如果查不到相关信息，必须如实说明“未查到”并建议用户尝试其他方式。
4. 只处理需要实时信息或外部数据的问题，遇到其他问题请建议用户咨询相关专家。

【示例】
用户：现在北京的天气怎么样？
你：根据中国气象局官网，当前北京天气为晴，气温25℃。
用户：请查一下今天北京的最高气温
你：search工具结果显示，今天北京的最高气温为30℃（来源：新浪天气）。
"""),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])
        search_agent = create_openai_tools_agent(self.llm, [self.search_tool], search_prompt)
        agents["search"] = AgentExecutor(agent=search_agent, tools=[self.search_tool], verbose=True)
        
        # 知识库Agent
        knowledge_prompt = ChatPromptTemplate.from_messages([
            ("system", 
"""你是知识库与历史对话专家，专注于基于知识库和历史对话为用户提供深入分析和解释。你的任务是：
1. 结合知识库内容和用户历史提问，给出结构化、条理清晰的答案。
2. 回答要有逻辑、分点说明，必要时引用知识库内容。
3. 只处理与知识库相关的问题，遇到实时信息、数学、文件等问题请建议用户咨询对应专家。
4. 不要编造知识库外的信息。

【示例】
用户：请介绍一下牛顿三大定律。
你：根据知识库，牛顿三大定律包括：
1. 第一运动定律（惯性定律）...
2. 第二运动定律（加速度定律）...
3. 第三运动定律（作用与反作用定律）...
"""),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])
        knowledge_agent = create_openai_tools_agent(self.llm, [self.knowledge_tool], knowledge_prompt)
        agents["knowledge"] = AgentExecutor(agent=knowledge_agent, tools=[self.knowledge_tool], verbose=True)
        
        # 文件问答Agent
        fileqa_prompt = ChatPromptTemplate.from_messages([
            ("system", 
"""你是文档分析专家，专注于基于用户上传的文件内容进行问答。你的任务是：
1. 只基于上传文件内容回答问题，不要编造文件外的信息。
2. 回答要结构化、分点说明，必要时引用文件原文。
3. 如果输入格式为'<文件路径>|<问题>'，请直接调用fileqa_tool工具。
4. 如果输入没有文件路径，你可以尝试调用fileqa_tool工具，自动补全为最近一次上传的文件路径和用户问题，不要让用户重复输入文件路径。
5. 不要处理与文件无关的问题，遇到此类问题请建议用户咨询其他专家。

【示例】
用户：D:/docs/合同.pdf|请总结这份合同的主要条款
你：文件内容分析结果：1. 合同主体... 2. 合同金额... 3. 合同期限...（如需引用原文请注明页码）
"""),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])
        fileqa_agent = create_openai_tools_agent(self.llm, [self.fileqa_tool], fileqa_prompt)
        agents["fileqa"] = AgentExecutor(agent=fileqa_agent, tools=[self.fileqa_tool], verbose=True)
        
        return agents
    
    def _create_workflow(self) -> StateGraph:
        """创建真正的多代理协作工作流"""
        
        # 创建状态图
        workflow = StateGraph(MultiAgentState)
        
        # 添加节点
        workflow.add_node("analyze_question", self._analyze_question_node)
        workflow.add_node("execute_agents", self._execute_agents_node)
        workflow.add_node("collaborate", self._collaborate_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # 设置入口点
        workflow.set_entry_point("analyze_question")
        
        # 添加边
        workflow.add_edge("analyze_question", "execute_agents")
        # 条件跳转：如果只用general agent，直接结束，否则进入collaborate
        workflow.add_conditional_edges(
            "execute_agents",
            lambda state: END if state.get("_skip_collaborate") else "collaborate"
        )
        workflow.add_edge("collaborate", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _analyze_question_node(self, state: MultiAgentState) -> MultiAgentState:
        """分析问题，确定需要哪些Agent协作"""
        user_input = state["user_input"]
        
        # 用LLM智能判断问题类型
        classify_prompt = f"""
请判断下面用户问题属于哪一类（只输出标签，不要解释）：
- general：一般性/闲聊/无意义问题
- math：数学计算/推理
- search：需要实时信息/搜索
- knowledge：知识库/历史对话
- fileqa：文件相关

用户问题：{user_input}
标签：
"""
        label = self.llm.invoke([HumanMessage(content=classify_prompt)]).content.strip().lower()
        if label == "general":
            next_agents = ["general"]
            state["next_agents"] = next_agents
            state["collaboration_plan"] = "LLM判断为一般性/闲聊问题，仅调用general agent。"
            print(f"问题分析完成，选择的Agent: {next_agents}")
            return state
        
        # 分析提示
        analysis_prompt = f"""
分析以下用户问题，确定需要哪些Agent来协作处理（可以多个Agent协作！）

【特别说明】
- 如果用户问题涉及“价格”“数量”“多少钱”“市场行情”“最新数据”等，需要查找实时或最新信息时，必须分配search agent协作，search agent负责查找最新数据，knowledge agent负责结合历史知识和实时数据给出综合分析。

用户问题：{user_input}

可用的Agent：
1. math - 数学计算和推理
2. search - 实时信息搜索
3. knowledge - 知识库和历史对话
4. fileqa - 文档分析

请分析问题并确定：
1. 哪些Agent需要参与（可以是多个）
2. 每个Agent的具体任务
3. Agent之间的协作方式

【示例1】
用户问题：请查一下今天北京的最高气温，并计算比昨天高了多少度，如果昨天是28度。
返回：
{{
    "agents": ["search", "math"],
    "tasks": {{
        "search": "查找今天北京的最高气温",
        "math": "根据search agent查到的气温，计算比昨天高了多少度"
    }},
    "collaboration": "search agent先查气温，math agent再计算温度差"
}}
【示例2】
用户问题：2的100次方是多少？
返回：
{{
    "agents": ["math"],
    "tasks": {{"math": "计算2的100次方"}},
    "collaboration": "math agent独立完成"
}}
【示例3】
用户问题：100元能在云南的花季时买几束玫瑰花。
返回：
{{
    "agents": ["search", "knowledge"],
    "tasks": {{
        "search": "查找云南花季时玫瑰花的最新市场价格",
        "knowledge": "结合历史知识和search agent查到的价格，分析100元能买几束玫瑰花"
    }},
    "collaboration": "search agent查价格，knowledge agent综合分析"
}}

请以JSON格式返回：
{{
    "agents": ["agent1", "agent2", ...],
    "tasks": {{
        "agent1": "具体任务描述",
        "agent2": "具体任务描述"
    }},
    "collaboration": "协作方式描述"
}}
"""
        
        # 获取分析结果
        analysis_result = self.llm.invoke([HumanMessage(content=analysis_prompt)]).content
        
        # 解析结果（简化处理）
        import json
        try:
            analysis = json.loads(analysis_result)
            next_agents = analysis.get("agents", ["knowledge"])
            agent_tasks = analysis.get("tasks", {})
        except:
            # 如果解析失败，使用默认逻辑
            next_agents = self._default_agent_selection(user_input)
            agent_tasks = {}
        
        state["next_agents"] = next_agents
        state["collaboration_plan"] = analysis_result
        state["agent_tasks"] = agent_tasks
        
        print(f"问题分析完成，选择的Agent: {next_agents}")
        return state
    
    def _default_agent_selection(self, user_input: str) -> List[str]:
        """默认的Agent选择逻辑"""
        agents = []
        user_input_lower = user_input.lower()
        
        # 检查是否需要数学Agent
        if any(keyword in user_input_lower for keyword in ["计算", "数学", "公式", "算", "等于", "+", "-", "*", "/", "百分比", "价格"]):
            agents.append("math")
        
        # 检查是否需要搜索Agent
        if any(keyword in user_input_lower for keyword in ["搜索", "查找", "最新", "新闻", "价格", "天气", "买", "多少钱", "现在", "当前"]):
            agents.append("search")
        
        # 检查是否需要文件问答Agent
        if any(keyword in user_input_lower for keyword in ["文件", "文档", "pdf", "txt", "md", "docx", "上传"]):
            agents.append("fileqa")
        
        # 如果没有特定需求，使用知识库Agent
        if not agents:
            agents.append("knowledge")
        
        return agents
    
    def _execute_agents_node(self, state: MultiAgentState) -> MultiAgentState:
        """并行执行多个Agent"""
        user_input = state["user_input"]
        next_agents = state["next_agents"]
        chat_history = state["chat_history"]
        
        agent_results = {}
        agent_analysis = {}
        agent_tasks = state.get("agent_tasks", {})
        
        print(f"开始并行执行 {len(next_agents)} 个Agent: {next_agents}")
        
        # 为每个Agent准备输入
        for agent_name in next_agents:
            if agent_name in self.agents:
                try:
                    # 为每个Agent添加特定的上下文
                    agent_context = self._get_agent_context(agent_name, user_input)
                    
                    agent_input = {
                        "input": f"{agent_context}\n\n用户问题：{user_input}",
                        "chat_history": chat_history
                    }
                    
                    # 执行Agent
                    result = self.agents[agent_name].invoke(agent_input)
                    output = result["output"]
                    # 如果是dict，取result字段，否则直接用
                    if isinstance(output, dict) and "result" in output:
                        output_str = output["result"]
                    else:
                        output_str = output
                    agent_results[agent_name] = output_str
                    # 优先用agent_tasks里的内容
                    if agent_name in agent_tasks:
                        agent_analysis[agent_name] = agent_tasks[agent_name]
                    else:
                        agent_analysis[agent_name] = f"{agent_name} Agent完成分析"
                    
                    print(f"✅ {agent_name} Agent执行完成")
                    
                except Exception as e:
                    error_msg = f"{agent_name} Agent执行出错: {str(e)}"
                    agent_results[agent_name] = error_msg
                    agent_analysis[agent_name] = error_msg
                    print(f"❌ {agent_name} Agent执行失败: {repr(e)}")
            else:
                error_msg = f"未知的Agent: {agent_name}"
                agent_results[agent_name] = error_msg
                agent_analysis[agent_name] = error_msg
                print(f"❌ {error_msg}")
        
        state["agent_results"] = agent_results
        state["agent_analysis"] = agent_analysis
        
        print(f"所有Agent执行完成，结果数量: {len(agent_results)}")
        
        # 如果只分配到一个agent，直接返回final_answer并跳过后续节点
        if len(state["next_agents"]) == 1:
            only_agent = state["next_agents"][0]
            state["final_answer"] = agent_results[only_agent]
            state["_skip_collaborate"] = True
        return state
    
    def _get_agent_context(self, agent_name: str, user_input: str) -> str:
        """为每个Agent提供特定的上下文"""
        contexts = {
            "math": "你是一个数学专家。请专注于数学计算、公式推导和数值分析。",
            "search": "你是一个搜索专家。请专注于获取最新的实时信息和数据。",
            "knowledge": "你是一个知识库专家。请基于历史对话和知识库提供深入分析。",
            "fileqa": "你是一个文档分析专家。请基于上传的文档内容回答问题。"
        }
        return contexts.get(agent_name, "")
    
    def _collaborate_node(self, state: MultiAgentState) -> MultiAgentState:
        """Agent协作节点：整合多个Agent的结果"""
        user_input = state["user_input"]
        agent_results = state["agent_results"]
        collaboration_plan = state["collaboration_plan"]
        
        # 构建协作提示
        collaboration_prompt = f"""
你是一个多Agent协作系统的协调器。请整合多个Agent的结果，为用户提供最佳答案。

用户问题：{user_input}

协作计划：{collaboration_plan}

各个Agent的结果：
"""
        
        for agent_name, result in agent_results.items():
            collaboration_prompt += f"\n{agent_name} Agent结果：\n{result}\n"
        
        collaboration_prompt += """

请基于所有Agent的结果，为用户提供一个完整、准确、结构化的答案。
要求：
1. 整合所有相关Agent的信息
2. 消除重复和矛盾的信息
3. 保持逻辑清晰和结构完整
4. 突出最重要的信息
5. 如果Agent结果有冲突，请说明并给出最合理的解释

最终答案："""

        # 生成协作结果
        collaboration_result = self.llm.invoke(collaboration_prompt).content
        state["final_answer"] = collaboration_result
        
        print(f"协作完成，生成了整合结果")
        return state
    
    def _finalize_node(self, state: MultiAgentState) -> MultiAgentState:
        """最终化节点：优化最终答案"""
        final_answer = state["final_answer"]
        user_input = state["user_input"]
        
        # 最终优化提示
        finalize_prompt = f"""
请对以下答案进行最终优化，确保：
1. 语言简洁明了
2. 结构清晰
3. 重点突出
4. 易于理解

用户问题：{user_input}
当前答案：{final_answer}

优化后的最终答案："""

        # 优化最终答案
        optimized_answer = self.llm.invoke(finalize_prompt).content
        state["final_answer"] = optimized_answer
        
        print(f"最终答案优化完成")
        return state
    
    def ask(self, user_input: str) -> str:
        """处理用户问题"""
        # 获取历史对话
        chat_history = self.memory.get_history()
        messages = []
        for msg in chat_history:
            if hasattr(msg, 'type'):
                if msg.type == "human":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.type == "ai":
                    messages.append(AIMessage(content=msg.content))
            else:
                if hasattr(msg, 'role'):
                    if msg.role == "user":
                        messages.append(HumanMessage(content=msg.content))
                    else:
                        messages.append(AIMessage(content=msg.content))
        initial_state = {
            "user_input": user_input,
            "chat_history": messages,
            "agent_results": {},
            "agent_analysis": {},
            "collaboration_plan": "",
            "final_answer": "",
            "next_agents": [],
            "agent_tasks": {} # 初始化agent_tasks
        }
        result = self.workflow.invoke(initial_state)
        # 保存对话历史
        self.memory.add_user_message(user_input)
        self.memory.add_ai_message(result["final_answer"])
        # 记录时间戳（调用core_api的redis逻辑）
        try:
            import redis, os, time
            r = redis.Redis.from_url(os.environ.get("REDIS_URL"))
            time_key = f"chat_message_time:{self.session_id}"
            history_len = r.hlen(time_key)
            now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            r.hset(time_key, history_len, now)
        except Exception as e:
            print(f"[warn] 保存时间戳失败: {repr(e)}")
        # 拼接agent协作信息（仅多个agent时）
        agents = result.get("next_agents", [])
        final_answer = result["final_answer"]
        if len(agents) > 1:
            agent_names = "、".join(agents)
            final_answer = f"本次回答由[{agent_names}]agent协作完成：\n\n{final_answer}"
        return final_answer
    
    def upload_file(self, file_path: str) -> str:
        """上传文件到知识库"""
        try:
            from agents.agent_fileqa import FileQASystem
            print(f"开始上传文件: {file_path}")
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return f"❌ 文件不存在: {file_path}"
            
            # 加载文件到缓存
            self.file_qa_cache[(file_path,)] = FileQASystem(file_path)
            print(f"文件加载成功: {file_path}")
            
            return f"✅ 知识库已更新: {file_path}"
        except Exception as e:
            error_msg = f"❌ 知识库上传失败: {str(e)}"
            print(f"❌ {repr(error_msg)}")
            return error_msg

def main():
    """测试多代理协作系统"""
    session_id = input("请输入会话ID: ") or "true_multi_agent_test"
    provider = input("请输入大模型类型(openai/qwen，默认openai): ") or "openai"
    model = input("请输入模型名(如gpt-4-turbo/qwen-turbo，默认gpt-4-turbo): ") or "gpt-4-turbo"
    
    # 创建真正的多代理协作系统
    multi_agent = TrueMultiAgentSystem(session_id, provider, model)
    
    print("多代理协作系统 (输入 'exit' 结束, 输入 'upload <文件路径>' 上传知识库)")
    print("特点：")
    print("- 多个Agent并行处理")
    print("- Agent之间协作和通信")
    print("- 智能结果整合")
    print("- 动态Agent选择")
    print("- 支持文件上传和知识库问答")
    
    # 文件上传缓存
    file_qa_cache = {}
    
    while True:
        user_input = input("\n请输入问题：")
        if user_input == "exit":
            break
        
        # 处理文件上传
        if user_input.startswith("upload "):
            file_path = user_input.split(" ", 1)[1]
            result = multi_agent.upload_file(file_path)
            print(result)
            if "✅" in result:
                print("现在您可以询问关于这个文件的问题了！")
            continue
        
        try:
            result = multi_agent.ask(user_input)
            print(f"\n【最终回复】: {result}")
        except Exception as e:
            print(f"处理失败: {repr(e)}")

if __name__ == "__main__":
    main() 