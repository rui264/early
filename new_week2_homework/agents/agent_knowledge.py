from langchain.tools import tool

def get_knowledge_tool(llm):
    @tool
    def knowledge_tool(query: str) -> dict:
        """知识库问答，结合历史上下文"""
        prompt = (
            "你是一位知识库专家，擅长结合历史对话、外部知识和专业知识为用户解答问题。请结合历史上下文和当前问题，给出权威、详细、结构化的解答。\n"
            "要求：1. 结合历史上下文，2. 结构化分点回答，3. 如有引用请标明来源，4. 结论清晰。\n"
            f"用户：{query}\n"
            "助手："
        )
        answer = llm.invoke(prompt).content
        return {"result": answer}
    return knowledge_tool