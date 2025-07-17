from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv

load_dotenv()


class DebateLLM:
    """处理与大语言模型的交互"""

    def __init__(self):
        self.llm = self._init_llm()

    def _init_llm(self) -> ChatOpenAI:
        """初始化LLM模型"""
        return ChatOpenAI(
            model_name="deepseek-chat",
            temperature=0.6,
            base_url=os.environ["DEEPSEEK_BASE_URL"],
            api_key=os.environ["DEEPSEEK_API_KEY"],
            max_tokens=1000  # 增加最大 token 限制，确保完整输出
        )

    def create_chain(self, prompt_template: str) -> LLMChain:
        """创建LLMChain"""
        prompt = PromptTemplate(
            input_variables=["topic", "history", "speakers", "position", "speaker_id", "mbti", "mbti_style"],
            template=prompt_template
        )
        return LLMChain(llm=self.llm, prompt=prompt)

    def get_argument_chain(self) -> LLMChain:
        """立论环节链条"""
        return self.create_chain("""
        你现在是辩论赛的{position}一辩（{speaker_id}），MBTI 类型为{mbti}，辩论风格{mbti_style}。

        请围绕辩题「{topic}」，结合你的 MBTI 辩论风格进行立论陈词：
        {history}

        要求：
        - 明确阐述己方核心立场
        - 给出2-3个有力论据
        - 字数严格控制在300-500字（必须完整输出，不得截断）
        - 语言正式，符合辩论赛风格
        - 回答中去除不必要的字符（比如'*'、'**'等），去除不必要的换行符
        """)

    def get_cross_examination_chain(self) -> LLMChain:
        """攻辩环节链条"""
        return self.create_chain("""
        你现在是辩论赛的{position}辩手（{speaker_id}），MBTI 类型为{mbti}，辩论风格{mbti_style}。
        辩题是「{topic}」，当前处于攻辩环节。

        攻辩规则：
        - 质询方需设计尖锐的逻辑问题，抓住对方漏洞
        - 回应方需冷静拆解对方逻辑，避免陷入陷阱

        历史发言参考：
        {history}

        要求：
        - 质询方发言≤200字，回应方发言≤300字
        - 必须体现{mbti_style}的辩论特点
        - 语言简洁有力，避免冗余
        - 回答中去除不必要的字符（比如'*'、'**'、'##'等），去除不必要的换行符
        """)

    def get_free_debate_chain(self) -> LLMChain:
        """自由辩论环节链条"""
        return self.create_chain("""
        你现在是辩论赛的{position}辩手（{speaker_id}），MBTI 类型为{mbti}，辩论风格{mbti_style}。
        辩题是「{topic}」，当前处于自由辩论环节。

        自由辩论规则：
        - 正反交替发言，每次发言需针对对方上一轮漏洞
        - 发言要简短（≤200字）、有针对性、攻击性强
        - 可适当运用{mbti_style}的特点进行反驳
        - 回答中去除不必要的字符（比如'*'、'**'等），去除不必要的换行符

        历史发言参考：
        {history}

        要求：输出纯粹的辩论内容，无需额外说明
        """)

    def get_summary_chain(self) -> LLMChain:
        """总结陈词环节链条"""
        return self.create_chain("""
        你现在是辩论赛的{position}四辩（{speaker_id}），MBTI 类型为{mbti}，辩论风格{mbti_style}。
        辩题是「{topic}」，请结合全场历史发言：

        {history}

        进行总结陈词，要求：
        - 梳理全场争议焦点（重点反驳对方漏洞）
        - 强化己方核心观点（结合{mbti_style}的特点）
        - 升华价值层面论述
        - 字数控制在400-600字
        - 回答中去除不必要的字符（比如'*'、'**'等），去除不必要的换行符
        """)