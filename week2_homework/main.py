from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Optional
from core_api import multi_agent_ask, get_chat_history, upload_knowledge_file
import logging
import os

app = FastAPI(
    title="多智能体问答系统API",
    description="提供多智能体问答、知识库上传和历史记录获取功能的API服务",
    version="1.0.0"
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 定义数据模型
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
#upload files

class UploadRequest(BaseModel):
    session_id: str
    file_path: str



class UploadResponse(BaseModel):
    success: bool
    message: str
    file_path: str


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

@app.post("/upload", response_model=UploadResponse)
def upload_file(request: UploadRequest):
    try:
        logger.info(f"Uploading file: {request.file_path} for session: {request.session_id}")

        # 调用核心函数
        result_message = upload_knowledge_file(
            session_id=request.session_id,
            file_path=request.file_path
        )

        return {
            "success": True,
            "message": result_message,
            "file_path": request.file_path
        }

    except HTTPException:
        raise  # 直接抛出已知HTTP异常
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(500, detail={
            "success": False,
            "message": f"文件处理失败: {str(e)}",
            "file_path": request.file_path
        })




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


