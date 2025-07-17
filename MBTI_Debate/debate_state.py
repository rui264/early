from typing import List, Dict
from constants import MBTI_STYLES


class DebateState:
    """管理辩论赛全局状态（轮次、环节、历史发言等）"""

    def __init__(self):
        self.current_round = 1  # 总轮次
        self.stage = "立论"  # 当前环节
        self.speaker_history = []  # 存储所有发言
        self.pro_team = ["pro1", "pro2", "pro3", "pro4"]  # 正方辩手
        self.opp_team = ["opp1", "opp2", "opp3", "opp4"]  # 反方辩手

        # 默认 MBTI 配置
        self.mbti_map = {
            "pro1": "INTJ", "pro2": "ENTJ", "pro3": "ENFP", "pro4": "INTP",
            "opp1": "ISTJ", "opp2": "ESTJ", "opp3": "ESFP", "opp4": "INFJ"
        }

    def add_speech(self, agent_id: str, content: str, analysis: list[str] = []):
        """记录一轮发言，新增 analysis 字段存储分析性内容列表"""
        self.speaker_history.append({
            "agent_id": agent_id,
            "round": self.current_round,
            "stage": self.stage,
            "content": content,      # 辩论正文
            "analysis": analysis     # 分析性内容列表
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