import os
from langchain_openai import ChatOpenAI
from langchain_qianwen import ChatQwen_v1

def get_llm(provider: str, model: str):
    if provider == "openai":
        return ChatOpenAI(
            model=model,
            base_url=os.environ["OPENAI_BASE_URL"],
            api_key=os.environ["OPENAI_API_KEY"],
            temperature=0
        )
    elif provider == "qwen":
        return ChatQwen_v1(
            model=model,
            base_url=os.environ["QWEN_BASE_URL"],
            api_key=os.environ["QWEN_API_KEY"],
            temperature=0
        )
    else:
        raise ValueError(f"不支持的provider: {provider}") 