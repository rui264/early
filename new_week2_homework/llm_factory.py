import os
from langchain_openai import ChatOpenAI
# from langchain_community.llms import Qwen, Qianfan

def get_llm(provider: str, model: str):
    provider = provider.lower()
    if provider == "openai":
        return ChatOpenAI(
            model=model,
            base_url=os.environ["OPENAI_BASE_URL"],
            api_key=os.environ["OPENAI_API_KEY"],
            temperature=0
        )
    elif provider == "qwen":
        # 千问Qwen兼容OpenAI协议，直接用ChatOpenAI即可
        return ChatOpenAI(
            model=model,
            base_url=os.environ["QWEN_BASE_URL"],
            api_key=os.environ["QWEN_API_KEY"],
            temperature=0
        )
    elif provider == "deepseek":
        return ChatOpenAI(
            model=model,
            base_url=os.environ["DEEPSEEK_BASE_URL"],
            api_key=os.environ["DEEPSEEK_API_KEY"],
            temperature=0
        )
    elif provider == "qianfan":
        return ChatOpenAI(
            model=model,
            base_url=os.environ["QIANFAN_BASE_URL"],
            api_key=os.environ["QIANFAN_API_KEY"],
            temperature=0
        )
    elif provider == "spark":
        # from langchain_community.llms.sparkdesk import SparkDesk
        from my_llms.sparkdesk import SparkDesk
        return SparkDesk(
            app_id=os.environ["SPARK_APP_ID"],
            api_key=os.environ["SPARK_API_KEY"],
            api_secret=os.environ["SPARK_API_SECRET"],
            # domain="generalv3",
            spark_url="wss://spark-api.xf-yun.com/v3.1/chat"
        )
    else:
        raise ValueError(f"不支持的provider: {provider}")