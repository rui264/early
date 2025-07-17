import re


def extract_analysis(text: str) -> tuple[str, list[str]]:
    """从文本中提取分析性内容（如【ESTP风格注】）"""
    # 匹配【任意内容】格式的文本
    pattern = r"【([^】]+)】"
    analysis_matches = re.findall(pattern, text)

    # 移除分析性内容，得到纯辩论内容
    debate_content = re.sub(pattern, "", text).strip()

    return debate_content, analysis_matches