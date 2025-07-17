from debate_engine import DebateEngine
from debate_manager import DebateManager

if __name__ == "__main__":
    # 定义辩题
    topic = "人工智能是否会取代人类工作"

    # 定义辩手的 MBTI 配置
    mbti_config = {
        "opp1": "ISTJ",
        "opp2": "ISFJ",
        "opp3": "INFJ",
        "opp4": "INTJ",
        "pro1": "ESTP",
        "pro2": "ESFP",
        "pro3": "ENFP",
        "pro4": "ENTP"
    }

    # 创建 DebateManager 实例，传入辩题
    manager = DebateManager(topic)

    # 根据 MBTI 配置设置辩手的 MBTI 类型
    for speaker_id, mbti in mbti_config.items():
        manager.state.set_mbti(speaker_id, mbti)

    # 创建 DebateEngine 实例，传入 DebateManager 实例
    engine = DebateEngine(manager)

    # 运行完整辩论
    history = engine.run_full_debate(free_debate_rounds=10)

    # 输出完整辩论记录
    print("\n\n=== 完整辩论记录 ===")
    for speech in history:
        print(f"\n{speech['agent_id']}（{speech['stage']}）:")
        print(f"  辩论内容: {speech['content']}")
        print(f"  分析内容: {speech['analysis']}")