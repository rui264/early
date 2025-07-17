from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import List, Dict
import os
from dotenv import load_dotenv
load_dotenv()


# ------------------------------
# 1. 基础配置与状态管理
# ------------------------------
class DebateState:
    """管理辩论赛全局状态（轮次、环节、历史发言等）"""

    def __init__(self):
        self.current_round = 1  # 总轮次
        self.stage = "立论"  # 当前环节：立论/攻辩/自由辩论/总结陈词
        self.speaker_history = []  # 存储所有发言
        self.pro_team = ["pro1", "pro2", "pro3", "pro4"]  # 正方辩手
        self.opp_team = ["opp1", "opp2", "opp3", "opp4"]  # 反方辩手

    def add_speech(self, agent_id: str, content: str):
        """记录一轮发言"""
        self.speaker_history.append({
            "agent_id": agent_id,
            "round": self.current_round,
            "stage": self.stage,
            "content": content
        })

    def next_round(self):
        """进入下一轮次"""
        self.current_round += 1

    def switch_stage(self, new_stage: str):
        """切换环节并重置轮次逻辑"""
        self.stage = new_stage
        if new_stage == "攻辩":
            self.current_round = 3  # 攻辩从第3轮开始
        elif new_stage == "自由辩论":
            self.current_round = 7  # 自由辩论从第7轮开始
        elif new_stage == "总结陈词":
            self.current_round = 8  # 总结陈词从第8轮开始


# ------------------------------
# 2. LLM 模型与通用工具
# ------------------------------
llm = ChatOpenAI(
    model_name="deepseek-chat",
    temperature=0.6,
    base_url=os.environ["DEEPSEEK_BASE_URL"],
    api_key=os.environ["DEEPSEEK_API_KEY"],
)


def create_chain(prompt_template: str) -> LLMChain:
    """快速创建 LangChain 的 LLMChain"""
    prompt = PromptTemplate(
        input_variables=["topic", "history", "speakers"],
        template=prompt_template
    )
    return LLMChain(llm=llm, prompt=prompt)


# ------------------------------
# 3. 各环节逻辑实现
# ------------------------------
class DebateManager:
    def __init__(self, topic: str):
        self.topic = topic  # 辩题
        self.state = DebateState()
        self.argument_chain = self._build_argument_chain()  # 立论环节链条
        self.cross_chain = self._build_cross_examination_chain()  # 攻辩环节链条
        self.free_chain = self._build_free_debate_chain()  # 自由辩论链条
        self.summary_chain = self._build_summary_chain()  # 总结陈词链条

    def _build_argument_chain(self) -> LLMChain:
        """立论环节：正反方一辩各一轮"""
        return create_chain("""
        你现在是辩论赛的{position}一辩，辩题是「{topic}」。
        请围绕辩题，结合以下历史发言（如果有），进行立论陈词：
        {history}

        要求：
        - 明确阐述己方核心立场
        - 给出2-3个有力论据
        - 字数控制在300-500字
        - 语言正式，符合辩论赛风格
        """)

    def _build_cross_examination_chain(self) -> LLMChain:
        """攻辩环节：正二↔反二、正三↔反三，每轮2条发言"""
        return create_chain("""
        你现在是辩论赛的{position}辩手（{speaker_id}），处于攻辩环节。
        辩题是「{topic}」，当前环节规则：
        - 正二质询反二 → 反二回应
        - 反二质询正二 → 正二回应
        - 正三质询反三 → 反三回应
        - 反三质询正三 → 正三回应
        - 质询方需设计逻辑问题，回应方需拆解逻辑

        历史发言参考：
        {history}

        要求：
        - 质询方发言≤200字，回应方发言≤300字
        - 必须包含针对性逻辑互动
        """)

    def _build_free_debate_chain(self) -> LLMChain:
        """自由辩论：正反交替多轮，支持简短攻击性发言"""
        return create_chain("""
        你现在是辩论赛的{position}辩手（{speaker_id}），处于自由辩论环节。
        辩题是「{topic}」，规则：
        - 正反交替发言（正方先开始）
        - 每次发言要简短（≤150字）、有针对性、攻击性强
        - 需针对对方漏洞进行反驳

        历史发言参考：
        {history}

        要求：输出纯粹的辩论内容，无需额外说明
        """)

    def _build_summary_chain(self) -> LLMChain:
        """总结陈词：正反方四辩各一轮"""
        return create_chain("""
        你现在是辩论赛的{position}四辩，辩题是「{topic}」。
        请结合全场历史发言：
        {history}

        进行总结陈词，要求：
        - 梳理全场争议焦点
        - 强化己方核心观点
        - 升华价值层面论述
        - 字数控制在400-600字
        """)

    # ------------------------------
    # 4. 核心流程执行
    # ------------------------------
    def run_argument_stage(self):
        """执行立论环节（轮次1-2）"""
        print(f"\n=== 立论环节（轮次{self.state.current_round}-{self.state.current_round + 1}）===")

        # 正方一辩（pro1）立论
        result = self.argument_chain.run(
            topic=self.topic,
            history="",  # 立论环节无前置发言
            speakers="正方一辩（pro1）",
            position="正方"
        )
        self.state.add_speech("pro1", result.strip())
        print(
            f"轮次{self.state.current_round} [{self.state.stage}] {self.state.speaker_history[-1]['agent_id']}: {result}")
        self.state.next_round()

        # 反方一辩（opp1）立论
        result = self.argument_chain.run(
            topic=self.topic,
            history=self.state.speaker_history[0]['content'],  # 参考正方立论
            speakers="反方一辩（opp1）",
            position="反方"
        )
        self.state.add_speech("opp1", result.strip())
        print(
            f"轮次{self.state.current_round} [{self.state.stage}] {self.state.speaker_history[-1]['agent_id']}: {result}")
        self.state.next_round()

        # 切换环节
        self.state.switch_stage("攻辩")

    def run_cross_examination_stage(self):
        """执行攻辩环节（轮次3-6）"""
        print(f"\n=== 攻辩环节（轮次{self.state.current_round}-{self.state.current_round + 3}）===")
        speakers_pair = [("pro2", "opp2"), ("pro3", "opp3")]  # 攻辩组合

        for idx, (pro_speaker, opp_speaker) in enumerate(speakers_pair, start=1):
            # 正方向反方质询（轮次3、5）
            self.state.current_round = 3 + 2 * (idx - 1)
            result = self.cross_chain.run(
                topic=self.topic,
                history=self._get_history_summary(),
                speakers=f"正方{pro_speaker}质询反方{opp_speaker}",
                position="正方",
                speaker_id=pro_speaker
            )
            self.state.add_speech(pro_speaker, result.strip())
            print(f"轮次{self.state.current_round} [{self.state.stage}] {pro_speaker}: {result}")
            self.state.next_round()

            # 反方回应（轮次4、6）
            result = self.cross_chain.run(
                topic=self.topic,
                history=self._get_history_summary(),
                speakers=f"反方{opp_speaker}回应{pro_speaker}",
                position="反方",
                speaker_id=opp_speaker
            )
            self.state.add_speech(opp_speaker, result.strip())
            print(f"轮次{self.state.current_round} [{self.state.stage}] {opp_speaker}: {result}")
            self.state.next_round()

        # 切换环节
        self.state.switch_stage("自由辩论")

    def run_free_debate_stage(self, max_rounds: int = 10):
        """执行自由辩论环节（轮次7开始，多轮交替）"""
        print(f"\n=== 自由辩论环节（轮次{self.state.current_round}开始，最多{max_rounds}轮）===")
        current_speaker_group = self.state.pro_team + self.state.opp_team  # 自由辩论可用辩手
        turn = 0  # 0=正方，1=反方

        for _ in range(max_rounds):
            # 选择当前发言辩手（简单轮询，可优化为策略选择）
            speaker_id = current_speaker_group[turn % len(current_speaker_group)]
            position = "正方" if speaker_id.startswith("pro") else "反方"

            result = self.free_chain.run(
                topic=self.topic,
                history=self._get_history_summary(),
                speakers=f"{position} {speaker_id}",
                position=position,
                speaker_id=speaker_id
            )
            self.state.add_speech(speaker_id, result.strip())
            print(f"轮次{self.state.current_round} [{self.state.stage}] {speaker_id}: {result.strip()}")

            self.state.next_round()
            turn += 1  # 切换发言方

        # 切换环节
        self.state.switch_stage("总结陈词")

    def run_summary_stage(self):
        """执行总结陈词环节（轮次8-9）"""
        print(f"\n=== 总结陈词环节（轮次{self.state.current_round}-{self.state.current_round + 1}）===")

        # 反方四辩（opp4）总结
        self.state.current_round = 8
        result = self.summary_chain.run(
            topic=self.topic,
            history=self._get_history_summary(),
            speakers="反方四辩（opp4）",
            position="反方"
        )
        self.state.add_speech("opp4", result.strip())
        print(f"轮次{self.state.current_round} [{self.state.stage}] opp4: {result}")
        self.state.next_round()

        # 正方四辩（pro4）总结
        result = self.summary_chain.run(
            topic=self.topic,
            history=self._get_history_summary(),
            speakers="正方四辩（pro4）",
            position="正方"
        )
        self.state.add_speech("pro4", result.strip())
        print(f"轮次{self.state.current_round} [{self.state.stage}] pro4: {result}")
        self.state.next_round()

    def _get_history_summary(self) -> str:
        """获取历史发言摘要（用于 prompt 上下文）"""
        summary = "\n".join([
            f"轮次{sp['round']} {sp['agent_id']}: {sp['content']}"
            for sp in self.state.speaker_history
        ])
        return summary if summary else "（无历史发言）"


# ------------------------------
# 5. 运行示例
# ------------------------------
if __name__ == "__main__":
    # 初始化辩论赛（设置辩题）
    debate = DebateManager(topic="人工智能是否会取代人类工作")

    # 依次执行各环节
    debate.run_argument_stage()  # 立论
    debate.run_cross_examination_stage()  # 攻辩
    debate.run_free_debate_stage(max_rounds=5)  # 自由辩论（示例跑5轮，可调整）
    debate.run_summary_stage()  # 总结陈词

    # 输出完整历史记录
    print("\n=== 完整辩论记录 ===")
    for speech in debate.state.speaker_history:
        print(f"轮次{speech['round']} [{speech['stage']}] {speech['agent_id']}: {speech['content']}")