from langchain.tools import tool

def get_math_tool(llm):
    @tool
    def math_tool(query: str) -> dict:
        """复杂数学推理与分步解答"""
        prompt = (
            "你是一位严谨的数学专家，善于分步推理和详细解释。请结合历史对话和当前问题，给出清晰、准确、结构化的数学解答。\n"
            "要求：1. 先分析问题类型，2. 分步推理，3. 明确公式和单位，4. 指出常见陷阱，5. 最后总结答案。\n"
            f"用户：{query}\n"
            "助手："
        )
        answer = llm.invoke(prompt).content
        return {"result": answer}
    return math_tool 