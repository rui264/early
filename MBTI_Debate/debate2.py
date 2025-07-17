from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()
from typing import List, Dict
import os
import random  # 新增：导入随机模块
from dotenv import load_dotenv

# MBTI 辩论风格映射表（用于 Prompt 注入）
MBTI_STYLES = {
    "INTJ": "逻辑严密，擅长构建系统论证框架，偏好使用演绎推理",
    "ENTJ": "直爽犀利，擅长战略布局，善于把握整体局势",
    "INTP": "思维敏捷，喜欢拆解对手逻辑漏洞，擅长提出新颖视角",
    "ENTP": "充满创意，辩论风格灵活多变，常以出乎意料的论据制胜",
    "ENFP": "富有感染力，善于调动情绪，擅长价值升华与共情表达",
    "INFJ": "视角深刻，能洞察问题本质，善于用案例和故事增强说服力",
    "ISTJ": "事实导向，数据和案例丰富，辩论风格严谨稳重",
    "ESTJ": "条理清晰，善于组织论据，擅长用权威数据支撑观点",
    "ESFP": "反应迅速，擅长临场应变，语言表达生动活泼",
    "ISFP": "观点温和但有韧性，常从细节切入，善于用具体事例反驳",
    "ISTP": "务实冷静，擅长分析实际问题，辩论风格简洁有力",
    "ESTP": "大胆果断，喜欢挑战传统观点，擅长快速反击",
    "ESFJ": "团队意识强，善于整合多方观点，语言表达亲切自然",
    "ISFJ": "细致入微，善于发现对手论证中的漏洞，擅长用事实反驳",
    "ENFJ": "极具领导力，擅长构建完整理论体系，语言富有煽动性",
    "INTP": "理论功底深厚，擅长用复杂模型分析问题，辩论风格理性"
}


# ------------------------------
# 1. 基础配置与状态管理
# ------------------------------
# 一个调度器agent
class DebateState:
    """管理辩论赛全局状态（轮次、环节、历史发言等）"""

    def __init__(self):
        self.current_round = 1  # 总轮次
        self.stage = "立论"  # 当前环节：立论/攻辩/自由辩论/总结陈词
        self.speaker_history = []  # 存储所有发言
        self.pro_team = ["pro1", "pro2", "pro3", "pro4"]  # 正方辩手
        self.opp_team = ["opp1", "opp2", "opp3", "opp4"]  # 反方辩手

        # 默认 MBTI 配置（可通过用户输入修改）
        self.mbti_map = {
            "pro1": "INTJ", "pro2": "ENTJ", "pro3": "ENFP", "pro4": "INTP",
            "opp1": "ISTJ", "opp2": "ESTJ", "opp3": "ESFP", "opp4": "INFJ"
        }

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

    def set_mbti(self, speaker_id: str, mbti: str):
        """设置辩手的 MBTI 类型"""
        if speaker_id in self.pro_team + self.opp_team:
            self.mbti_map[speaker_id] = mbti.upper()
            print(f"已设置 {speaker_id} 的 MBTI 为 {self.mbti_map[speaker_id]}")
        else:
            print(f"无效的辩手 ID: {speaker_id}")

    def get_mbti_style(self, speaker_id: str) -> str:
        """获取辩手的 MBTI 辩论风格描述"""
        mbti = self.mbti_map.get(speaker_id, "未知")
        return MBTI_STYLES.get(mbti, f"具有{mbti}类型的典型辩论风格")


# ------------------------------
# 2. LLM 模型与通用工具
# ------------------------------
llm = ChatOpenAI(
    model_name="deepseek-chat",
    temperature=0.6,
    base_url=os.environ["DEEPSEEK_BASE_URL"],
    api_key=os.environ["DEEPSEEK_API_KEY"],
    max_tokens=1000  # 增加最大 token 限制，确保完整输出
)


def create_chain(prompt_template: str) -> LLMChain:
    """快速创建 LangChain 的 LLMChain"""
    prompt = PromptTemplate(
        input_variables=["topic", "history", "speakers", "position", "speaker_id", "mbti", "mbti_style"],
        template=prompt_template
    )
    return LLMChain(llm=llm, prompt=prompt)


# ------------------------------
# 3. 各环节逻辑实现
# ------------------------------
class DebateManager:
    def __init__(self, topic: str = None):
        if topic:
            self.topic = topic
        else:
            self.topic = self._get_topic_from_user()

        self.state = DebateState()
        self._init_mbti_from_user()  # 初始化 MBTI
        self.argument_chain = self._build_argument_chain()  # 立论环节链条
        self.cross_chain = self._build_cross_examination_chain()  # 攻辩环节链条
        self.free_chain = self._build_free_debate_chain()  # 自由辩论链条
        self.summary_chain = self._build_summary_chain()  # 总结陈词链条

    def _get_topic_from_user(self) -> str:
        """从用户输入获取辩题"""
        print("\n=== 辩论赛准备 ===")
        default_topic = "人工智能是否会取代人类工作"
        topic = input(f"请输入辩题（默认：{default_topic}）：").strip()
        return topic if topic else default_topic

    def _init_mbti_from_user(self):
        """从用户输入初始化辩手的 MBTI 类型"""
        print("\n=== 设置辩手 MBTI 类型 ===")
        print("（直接回车使用默认值，MBTI 类型需为标准 4 字母代码，如 INTJ、ENFP）")

        for speaker_id in self.state.pro_team + self.state.opp_team:
            default_mbti = self.state.mbti_map[speaker_id]
            mbti = input(f"请输入 {speaker_id} 的 MBTI 类型（默认 {default_mbti}）：").strip()

            if mbti:
                if mbti.upper() in MBTI_STYLES:
                    self.state.set_mbti(speaker_id, mbti.upper())
                else:
                    print(f"无效的 MBTI 类型，使用默认值 {default_mbti}")
            else:
                print(f"{speaker_id} 使用默认 MBTI：{default_mbti}")

    def _build_argument_chain(self) -> LLMChain:
        """立论环节：正反方一辩各一轮"""
        return create_chain("""
        你现在是辩论赛的{position}一辩（{speaker_id}），MBTI 类型为{mbti}，辩论风格{mbti_style}。

        请围绕辩题「{topic}」，结合你的 MBTI 辩论风格进行立论陈词：
        {history}

        要求：
        - 明确阐述己方核心立场
        - 给出2-3个有力论据
        - 字数严格控制在300-500字（必须完整输出，不得截断）
        - 语言正式，符合辩论赛风格
        """)

    def _build_cross_examination_chain(self) -> LLMChain:
        """攻辩环节：正二↔反二、正三↔反三，每轮2条发言"""
        return create_chain("""
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
        """)

    def _build_free_debate_chain(self) -> LLMChain:
        """自由辩论：正反交替多轮，支持简短攻击性发言"""
        return create_chain("""
        你现在是辩论赛的{position}辩手（{speaker_id}），MBTI 类型为{mbti}，辩论风格{mbti_style}。
        辩题是「{topic}」，当前处于自由辩论环节。

        自由辩论规则：
        - 正反交替发言，每次发言需针对对方上一轮漏洞
        - 发言要简短（≤200字）、有针对性、攻击性强
        - 可适当运用{mbti_style}的特点进行反驳

        历史发言参考：
        {history}

        要求：输出纯粹的辩论内容，无需额外说明
        """)

    def _build_summary_chain(self) -> LLMChain:
        """总结陈词：正反方四辩各一轮"""
        return create_chain("""
        你现在是辩论赛的{position}四辩（{speaker_id}），MBTI 类型为{mbti}，辩论风格{mbti_style}。
        辩题是「{topic}」，请结合全场历史发言：

        {history}

        进行总结陈词，要求：
        - 梳理全场争议焦点（重点反驳对方漏洞）
        - 强化己方核心观点（结合{mbti_style}的特点）
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
            history="",
            speakers="正方一辩（pro1）",
            position="正方",
            speaker_id="pro1",
            mbti=self.state.mbti_map["pro1"],
            mbti_style=self.state.get_mbti_style("pro1")
        )
        self.state.add_speech("pro1", result.strip())
        print(f"轮次{self.state.current_round} [{self.state.stage}] {self.state.speaker_history[-1]['agent_id']}:")
        print(result.strip())
        self.state.next_round()

        # 反方一辩（opp1）立论
        result = self.argument_chain.run(
            topic=self.topic,
            history=self.state.speaker_history[0]['content'],
            speakers="反方一辩（opp1）",
            position="反方",
            speaker_id="opp1",
            mbti=self.state.mbti_map["opp1"],
            mbti_style=self.state.get_mbti_style("opp1")
        )
        self.state.add_speech("opp1", result.strip())
        print(f"轮次{self.state.current_round} [{self.state.stage}] {self.state.speaker_history[-1]['agent_id']}:")
        print(result.strip())
        self.state.next_round()

        # 切换环节
        self.state.switch_stage("攻辩")

    def run_cross_examination_stage(self):
        """执行攻辩环节（轮次3 - 6）"""
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
                speaker_id=pro_speaker,
                mbti=self.state.mbti_map[pro_speaker],
                # 修正此处的方法调用语法
                mbti_style=self.state.get_mbti_style(pro_speaker)
            )
            self.state.add_speech(pro_speaker, result.strip())
            print(f"轮次{self.state.current_round} [{self.state.stage}] {pro_speaker}:")
            print(result.strip())
            self.state.next_round()

            # 反方回应（轮次4、6）
            result = self.cross_chain.run(
                topic=self.topic,
                history=self._get_history_summary(),
                speakers=f"反方{opp_speaker}回应{pro_speaker}",
                position="反方",
                speaker_id=opp_speaker,
                mbti=self.state.mbti_map[opp_speaker],
                # 修正此处的方法调用语法
                mbti_style=self.state.get_mbti_style(opp_speaker)
            )
            self.state.add_speech(opp_speaker, result.strip())
            print(f"轮次{self.state.current_round} [{self.state.stage}] {opp_speaker}:")
            print(result.strip())
            self.state.next_round()

        # 切换环节
        self.state.switch_stage("自由辩论")

    def run_free_debate_stage(self, max_rounds: int = 10):
        """执行自由辩论环节（轮次7开始，多轮交替，正方先开始）"""
        print(f"\n=== 自由辩论环节（轮次{self.state.current_round}开始，最多{max_rounds}轮）===")

        # 拆分正方和反方辩手池
        pro_pool = self.state.pro_team  # 正方辩手：["pro1", "pro2", "pro3", "pro4"]
        opp_pool = self.state.opp_team  # 反方辩手：["opp1", "opp2", "opp3", "opp4"]

        turn = 0  # 0=正方发言，1=反方发言（确保正方先开始）

        for _ in range(max_rounds):
            if turn % 2 == 0:
                # 正方随机选一位辩手发言
                speaker_id = random.choice(pro_pool)
                position = "正方"
            else:
                # 反方随机选一位辩手发言
                speaker_id = random.choice(opp_pool)
                position = "反方"

            # 生成发言
            result = self.free_chain.run(
                topic=self.topic,
                history=self._get_history_summary(),
                speakers=f"{position} {speaker_id}",
                position=position,
                speaker_id=speaker_id,
                mbti=self.state.mbti_map[speaker_id],
                mbti_style=self.state.get_mbti_style(speaker_id)
            )
            self.state.add_speech(speaker_id, result.strip())
            print(f"轮次{self.state.current_round} [{self.state.stage}] {speaker_id}:")
            print(result.strip())

            self.state.next_round()
            turn += 1  # 切换发言方（正方→反方→正方...）

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
            position="反方",
            speaker_id="opp4",
            mbti=self.state.mbti_map["opp4"],
            mbti_style=self.state.get_mbti_style("opp4")
        )
        self.state.add_speech("opp4", result.strip())
        print(f"轮次{self.state.current_round} [{self.state.stage}] opp4:")
        print(result.strip())
        self.state.next_round()

        # 正方四辩（pro4）总结
        result = self.summary_chain.run(
            topic=self.topic,
            history=self._get_history_summary(),
            speakers="正方四辩（pro4）",
            position="正方",
            speaker_id="pro4",
            mbti=self.state.mbti_map["pro4"],
            mbti_style=self.state.get_mbti_style("pro4")
        )
        self.state.add_speech("pro4", result.strip())
        print(f"轮次{self.state.current_round} [{self.state.stage}] pro4:")
        print(result.strip())
        self.state.next_round()

    def _get_history_summary(self) -> str:
        """获取历史发言摘要（用于 prompt 上下文）"""
        if not self.state.speaker_history:
            return "（无历史发言）"

        summary = "\n\n".join([
            f"轮次{sp['round']} [{sp['stage']}] {sp['agent_id']}（{self.state.mbti_map[sp['agent_id']]}）:\n{sp['content']}"
            for sp in self.state.speaker_history
        ])
        return summary

class DebateEngine:
    """对外提供的辩论引擎接口"""
    def __init__(self, topic: str = None, mbti_config: Dict[str, str] = None):
        self.manager = DebateManager(topic)
        if mbti_config:
            for speaker_id, mbti in mbti_config.items():
                self.manager.state.set_mbti(speaker_id, mbti)

    def run_full_debate(self, free_debate_rounds: int = 10) -> List[Dict]:
        """运行完整辩论流程并返回记录"""
        self.manager.run_argument_stage()
        self.manager.run_cross_examination_stage()
        self.manager.run_free_debate_stage(max_rounds=free_debate_rounds)
        self.manager.run_summary_stage()
        return self.manager.state.speaker_history

    def get_debate_topic(self) -> str:
        """获取当前辩题"""
        return self.manager.topic


# ------------------------------
# 5. 运行示例
# ------------------------------
if __name__ == "__main__":
    engine=DebateEngine(
        topic="人工智能是否应该被赋予法律权利",
        mbti_config={
            "opp1": "ISTJ",
            "opp2": "ISFJ",
            "opp3": "INFJ",
            "opp4": "INTJ",
            "pro1": "ESTP",
            "pro2": "ESFP",
            "pro3": "ENFP",
            "pro4": "ENTP"
        }
    )
    # 历史记录以列表的结构储存 每一个元素是一个字典
    history = engine.run_full_debate(free_debate_rounds=10)
    print("\n\n=== 完整辩论记录 ===")
    for speech in history:
        mbti = engine.manager.state.mbti_map[speech['agent_id']]
        print(f"轮次{speech['round']} [{speech['stage']}] {speech['agent_id']}（{mbti}）:")
        print(speech['content'])
        print("-" * 50)
    """
    举例如下：
    [
    {
        "agent_id": "pro1",
        "round": 1,
        "stage": "立论",
        "content": "正方一辩陈词：人工智能将大幅提高生产力，但不会完全取代人类..."
    },
    {
        "agent_id": "opp1",
        "round": 2,
        "stage": "立论",
        "content": "反方一辩陈词：随着AI技术发展，重复性工作必将被自动化取代..."
    },
    {
        "agent_id": "pro2",
        "round": 3,
        "stage": "攻辩",
        "content": "正方二辩质询：请问对方辩友，如何解释医疗领域AI仅作为辅助工具？"
    },
    # 更多记录...
    ]
    """

