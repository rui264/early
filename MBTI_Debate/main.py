from debate_engine import DebateEngine

if __name__ == "__main__":
    # 初始化辩论引擎
    engine = DebateEngine(
        topic="钱是不是万恶之源？",
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

    # 运行完整辩论
    history = engine.run_full_debate(free_debate_rounds=10)

    # 输出完整辩论记录
    print("\n\n=== 完整辩论记录 ===")
    for speech in history:
        print(f"\n{speech['agent_id']}（{speech['stage']}）:")
        print(f"  辩论内容: {speech['content']}")
        # print(f"  分析内容: {speech['analysis']}")



# fastapi调用指南
"""
from fastapi import FastAPI
from debate_engine import DebateEngine

app = FastAPI()

@app.get("/debate")
async def run_debate(
        topic: str = "人工智能是否会取代人类工作", 
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
):
    engine = DebateEngine(topic=topic, mbti_config=mbti_config)
    # 运行辩论流程并流式输出发言内容
    def generate():
        for speech in engine.run_full_debate(free_debate_rounds=10):
            yield str(speech).encode() + b'\n'
    return generate()
"""