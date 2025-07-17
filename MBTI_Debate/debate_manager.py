from typing import List, Dict
import random
from debate_state import DebateState
from llm_client import DebateLLM
from constants import STAGES
import re
from text_utils import extract_analysis  # 导入文本处理工具


class DebateManager:
    """管理辩论流程"""

    def __init__(self, topic: str = None):
        self.topic = topic if topic else self._get_topic_from_user()
        self.state = DebateState()
        self.llm = DebateLLM()
        self._init_chains()

    def _init_chains(self):
        """初始化各环节的链条"""
        self.argument_chain = self.llm.get_argument_chain()
        self.cross_chain = self.llm.get_cross_examination_chain()
        self.free_chain = self.llm.get_free_debate_chain()
        self.summary_chain = self.llm.get_summary_chain()

    def _get_topic_from_user(self) -> str:
        """从用户输入获取辩题"""
        print("\n=== 辩论赛准备 ===")
        default_topic = "人工智能是否会取代人类工作"
        topic = input(f"请输入辩题（默认：{default_topic}）：").strip()
        return topic if topic else default_topic

    def init_mbti_from_user(self):
        """从用户输入初始化辩手的 MBTI 类型"""
        print("\n=== 设置辩手 MBTI 类型 ===")
        print("（直接回车使用默认值，MBTI 类型需为标准 4 字母代码，如 INTJ、ENFP）")

        for speaker_id in self.state.pro_team + self.state.opp_team:
            default_mbti = self.state.mbti_map[speaker_id]
            mbti = input(f"请输入 {speaker_id} 的 MBTI 类型（默认 {default_mbti}）：").strip()

            if mbti:
                if mbti.upper() in self.state.MBTI_STYLES:
                    self.state.set_mbti(speaker_id, mbti.upper())
                else:
                    print(f"无效的 MBTI 类型，使用默认值 {default_mbti}")
            else:
                print(f"{speaker_id} 使用默认 MBTI：{default_mbti}")

    def _get_history_summary(self) -> str:
        """获取历史发言摘要"""
        if not self.state.speaker_history:
            return "（无历史发言）"

        summary = "\n\n".join([
            f"轮次{sp['round']} [{sp['stage']}] {sp['agent_id']}（{self.state.mbti_map[sp['agent_id']]}）:\n{sp['content']}"
            for sp in self.state.speaker_history
        ])
        return summary

    def run_argument_stage(self):
        """执行立论环节"""
        print(f"\n=== {STAGES['ARGUMENT']}环节（轮次{self.state.current_round}-{self.state.current_round + 1}）===")

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
        # 调用 extract_analysis 拆分内容
        debate_content, analysis_list = extract_analysis(result)
        self.state.add_speech("pro1", debate_content, analysis_list)
        print(f"轮次{self.state.current_round} [{self.state.stage}] {self.state.speaker_history[-1]['agent_id']}:")
        print(debate_content)  # 打印辩论正文
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
        debate_content, analysis_list = extract_analysis(result)
        self.state.add_speech("opp1", debate_content, analysis_list)
        print(f"轮次{self.state.current_round} [{self.state.stage}] {self.state.speaker_history[-1]['agent_id']}:")
        print(debate_content)  # 打印辩论正文
        self.state.next_round()

        # 切换环节
        self.state.switch_stage(STAGES["CROSS_EXAMINATION"])

    def run_cross_examination_stage(self):
        """执行攻辩环节"""
        print(
            f"\n=== {STAGES['CROSS_EXAMINATION']}环节（轮次{self.state.current_round}-{self.state.current_round + 3}）===")
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
                mbti_style=self.state.get_mbti_style(pro_speaker)
            )
            debate_content, analysis_list = extract_analysis(result)
            self.state.add_speech(pro_speaker, debate_content, analysis_list)
            print(f"轮次{self.state.current_round} [{self.state.stage}] {pro_speaker}:")
            print(debate_content)  # 打印辩论正文
            self.state.next_round()

            # 反方回应（轮次4、6）
            result = self.cross_chain.run(
                topic=self.topic,
                history=self._get_history_summary(),
                speakers=f"反方{opp_speaker}回应{pro_speaker}",
                position="反方",
                speaker_id=opp_speaker,
                mbti=self.state.mbti_map[opp_speaker],
                mbti_style=self.state.get_mbti_style(opp_speaker)
            )
            debate_content, analysis_list = extract_analysis(result)
            self.state.add_speech(opp_speaker, debate_content, analysis_list)
            print(f"轮次{self.state.current_round} [{self.state.stage}] {opp_speaker}:")
            print(debate_content)  # 打印辩论正文
            self.state.next_round()

        # 切换环节
        self.state.switch_stage(STAGES["FREE_DEBATE"])

    def run_free_debate_stage(self, max_rounds: int = 10):
        """执行自由辩论环节"""
        print(f"\n=== {STAGES['FREE_DEBATE']}环节（轮次{self.state.current_round}开始，最多{max_rounds}轮）===")

        # 拆分正方和反方辩手池
        pro_pool = self.state.pro_team  # 正方辩手
        opp_pool = self.state.opp_team  # 反方辩手

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
            debate_content, analysis_list = extract_analysis(result)
            self.state.add_speech(speaker_id, debate_content, analysis_list)
            print(f"轮次{self.state.current_round} [{self.state.stage}] {speaker_id}:")
            print(debate_content)  # 打印辩论正文

            self.state.next_round()
            turn += 1  # 切换发言方

        # 切换环节
        self.state.switch_stage(STAGES["SUMMARY"])

    def run_summary_stage(self):
        """执行总结陈词环节"""
        print(f"\n=== {STAGES['SUMMARY']}环节（轮次{self.state.current_round}-{self.state.current_round + 1}）===")

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
        debate_content, analysis_list = extract_analysis(result)
        self.state.add_speech("opp4", debate_content, analysis_list)
        print(f"轮次{self.state.current_round} [{self.state.stage}] opp4:")
        print(debate_content)  # 打印辩论正文
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
        debate_content, analysis_list = extract_analysis(result)
        self.state.add_speech("pro4", debate_content, analysis_list)
        print(f"轮次{self.state.current_round} [{self.state.stage}] pro4:")
        print(debate_content)  # 打印辩论正文
        self.state.next_round()