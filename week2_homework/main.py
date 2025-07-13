from fastapi import FastAPI, HTTPException, Query, UploadFile, File  # 新增UploadFile和File
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import logging
from core_api import multi_agent_ask, get_chat_history, upload_knowledge_file

app = FastAPI(
    title="多智能体问答系统API",
    description="提供多智能体问答、知识库上传和历史记录获取功能的API服务",
    version="1.0.0"
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 确保上传目录存在（自动创建）
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# 定义数据模型（保持其他模型不变）
class ChatRequest(BaseModel):
    session_id: str
    question: str
    provider: Optional[str] = "openai"
    model: Optional[str] = "gpt-4-turbo"


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    model_used: str
    success: bool


class HistoryResponse(BaseModel):
    history: List[Dict]
    success: bool


# 【修改】文件上传响应模型（保持不变）
class UploadResponse(BaseModel):
    success: bool
    message: str
    file_path: str


# 【重点修改】文件上传接口：支持前端表单上传文件
@app.post("/upload", response_model=UploadResponse)
def upload_file(
        session_id: str = Query(..., description="会话ID"),
        file: UploadFile = File(..., description="要上传的文件（支持PDF、TXT等）")
):
    try:
        # 1. 保存上传的文件到本地
        file_save_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_save_path, "wb") as f:
            f.write(file.file.read())  # 读取上传的文件内容并保存

        # 2. 调用核心函数处理文件（传入保存后的本地路径）
        result_message = upload_knowledge_file(
            session_id=session_id,
            file_path=file_save_path  # 传入实际保存的路径
        )

        return {
            "success": True,
            "message": result_message,
            "file_path": file_save_path
        }

    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": f"文件处理失败: {str(e)}",
                "file_path": file.filename if file else "未知文件"
            }
        )

# 其他接口保持不变（chat_via_get、chat_via_post、get_history）
# ...
# 根路径
@app.get("/")
def read_root():
    return {"欢迎使用": "多智能体问答系统API", "文档": "/docs"}


# GET方式聊天接口
@app.get("/chat/{session_id}", response_model=ChatResponse)
def chat_via_get(
        session_id: str,
        question: str = Query(..., min_length=1, max_length=500),
        provider: str = Query("openai", regex="^(openai|qwen)$"),
        model: str = Query("gpt-4-turbo", regex="^(gpt-3.5-turbo|gpt-4-turbo|qwen-turbo)$")
):
    try:
        logger.info(f"Processing question: {question} with {model}")

        # 调用核心API获取真实模型响应
        answer = multi_agent_ask(
            session_id=session_id,
            question=question,
            provider=provider,
            model=model
        )

        return {
            "answer": answer,
            "session_id": session_id,
            "model_used": model,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error in chat_via_get: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"模型服务错误: {str(e)}"
        )


# POST方式聊天接口
@app.post("/chat", response_model=ChatResponse)
def chat_via_post(request: ChatRequest):
    try:
        logger.info(f"Processing question: {request.question} with {request.model}")

        answer = multi_agent_ask(
            session_id=request.session_id,
            question=request.question,
            provider=request.provider,
            model=request.model
        )

        return {
            "answer": answer,
            "session_id": request.session_id,
            "model_used": request.model,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error in chat_via_post: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"模型服务错误: {str(e)}"
        )
# 获取历史记录（现在使用core_api的真实历史记录）
@app.get("/history", response_model=HistoryResponse)
def get_history(session_id: str = Query(..., min_length=1)):
    try:
        history = get_chat_history(session_id)
        return {
            "history": history,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"历史记录获取失败: {str(e)}"
        )
