from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import List, Dict, Optional
from core_api import multi_agent_ask, get_chat_history, upload_knowledge_file, delete_chat_history, rename_session_id
import logging
import os
from pathlib import Path

app = FastAPI(
    title="多智能体问答系统API",
    description="提供多智能体问答、知识库上传和历史记录获取功能的API服务",
    version="1.0.0"
)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或者写成 ["http://localhost:8080", "http://你的前端IP:端口"] 更安全
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建上传目录
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


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
    question_time: str  # 新增：返回提问时间


class HistoryResponse(BaseModel):
    history: List[Dict]
    success: bool


class UploadResponse(BaseModel):
    success: bool
    message: str
    file_path: str


class RenameResponse(BaseModel):
    success: bool
    message: str
    new_session_id: str


# 根路径
@app.get("/")
def read_root():
    return {"欢迎使用": "多智能体问答系统API", "文档": "/docs"}


# GET方式聊天接口（异步化处理）
@app.get("/chat/{session_id}", response_model=ChatResponse)
async def chat_via_get(
        session_id: str,
        question: str = Query(..., min_length=1, max_length=500),
        provider: str = Query("openai", regex="^(openai|qwen)$"),
        model: str = Query("gpt-4-turbo", regex="^(gpt-3.5-turbo|gpt-4-turbo|qwen-turbo)$")
):
    try:
        logger.info(f"Processing question: {question} with {model}")

        # 异步执行耗时操作（避免阻塞事件循环）
        result = await run_in_threadpool(
            multi_agent_ask,
            session_id=session_id,
            question=question,
            provider=provider,
            model=model
        )

        return {
            "answer": result["answer"],  # 修复：提取dict中的answer字段
            "session_id": session_id,
            "model_used": model,
            "success": True,
            "question_time": result["question_time"]  # 新增时间戳返回
        }
    except Exception as e:
        logger.error(f"Error in chat_via_get: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"模型服务错误: {str(e)}"
        )


# POST方式聊天接口（异步化处理）
@app.post("/chat", response_model=ChatResponse)
async def chat_via_post(request: ChatRequest):
    try:
        logger.info(f"Processing question: {request.question} with {request.model}")

        # 异步执行耗时操作
        result = await run_in_threadpool(
            multi_agent_ask,
            session_id=request.session_id,
            question=request.question,
            provider=request.provider,
            model=request.model
        )

        return {
            "answer": result["answer"],  # 修复：提取dict中的answer字段
            "session_id": request.session_id,
            "model_used": request.model,
            "success": True,
            "question_time": result["question_time"]
        }
    except Exception as e:
        logger.error(f"Error in chat_via_post: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"模型服务错误: {str(e)}"
        )


# 文件上传接口（修复上传逻辑，支持前端文件流）
@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        # 保存上传的文件到服务器
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()  # 异步读取文件内容
            f.write(content)

        logger.info(f"Uploading file: {file_path} for session: {session_id}")

        # 异步处理文件
        result_message = await run_in_threadpool(
            upload_knowledge_file,
            session_id=session_id,
            file_path=str(file_path)
        )

        return {
            "success": True,
            "message": result_message,
            "file_path": str(file_path)
        }

    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"文件处理失败: {str(e)}"
        )


# 获取历史记录（异步化）
@app.get("/history", response_model=HistoryResponse)
async def get_history(session_id: str = Query(..., min_length=1)):
    try:
        # 异步获取历史
        history = await run_in_threadpool(
            get_chat_history,
            session_id=session_id
        )
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


# 新增：删除历史记录接口
@app.delete("/history/{session_id}")
async def delete_history(session_id: str):
    try:
        result = await run_in_threadpool(
            delete_chat_history,
            session_id=session_id
        )
        return {"success": result, "message": "历史记录已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 新增：重命名会话接口
@app.post("/rename-session", response_model=RenameResponse)
async def rename_session(
    old_session_id: str = Form(...),
    new_session_id: str = Form(...)
):
    try:
        result = await run_in_threadpool(
            rename_session_id,
            old_session_id=old_session_id,
            new_session_id=new_session_id
        )
        return {
            "success": result,
            "message": "会话重命名成功",
            "new_session_id": new_session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))