# 测试上传文件函数的功能
from core_api import upload_knowledge_file

session_id = "abc123"
file_path = r"D:\大二下资料\设计思维\6,思维发散.pdf"  # 替换为实际文件路径

msg = upload_knowledge_file(session_id, file_path)
print(msg)