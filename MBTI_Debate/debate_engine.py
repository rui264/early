from typing import List, Dict, Callable, Optional
from debate_manager import DebateManager

class DebateEngine:
    def __init__(self, manager):
        self.manager = manager
        self.callback = None

    def run_full_debate(self, free_debate_rounds: int = 10):
        """运行完整辩论流程，并以生成器的方式流式输出每条发言内容"""
        def stage_callback(speech):
            yield speech

        stages = [
            self.manager.run_argument_stage,
            self.manager.run_cross_examination_stage,
            lambda: self.manager.run_free_debate_stage(max_rounds=free_debate_rounds),
            self.manager.run_summary_stage
        ]

        for stage in stages:
            prev_count = len(self.manager.state.speaker_history)
            stage()
            new_speeches = self.manager.state.speaker_history[prev_count:]
            for speech in new_speeches:
                yield speech

    def _run_stage_with_callback(self, stage_func):
        """执行环节并触发回调"""
        prev_count = len(self.manager.state.speaker_history)
        stage_func()
        new_speeches = self.manager.state.speaker_history[prev_count:]
        if self.callback:
            for speech in new_speeches:
                self.callback(speech)  # 触发回调，传入单条发言
    def get_debate_state(self):
        """获取当前辩论状态"""
        return self.manager.state