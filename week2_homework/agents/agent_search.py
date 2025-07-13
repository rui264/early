from langchain_community.tools import DuckDuckGoSearchRun
from langchain.tools import tool

def get_search_tool(llm):
    search = DuckDuckGoSearchRun()
    @tool
    def search_tool(query: str) -> dict:
        """互联网搜索与结构化总结"""
        search_result = search.run(query)
        prompt = (
            "你是一位互联网信息专家，擅长检索和整合最新权威信息。请结合当前问题和以下搜索结果，为用户做出权威、简明、结构化的回答。\n"
            "要求：1. 筛选有用信息，去除重复和无关内容；2. 结构化分点总结；3. 如有多条信息，按条列出。\n"
            f"用户问题：{query}\n"
            f"搜索结果：{search_result}\n"
            "助手："
        )
        answer = llm.invoke(prompt).content
        return {"result": answer}
    return search_tool 