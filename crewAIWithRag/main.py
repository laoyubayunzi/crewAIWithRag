# 导入依赖包
import os
import sys
import re
import uuid
import time
import json
import asyncio
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from langchain_openai import ChatOpenAI
from crew import CrewtestprojectCrew



# 模型全局参数配置  根据自己的实际情况进行调整
# openai模型相关配置 根据自己的实际情况进行调整
OPENAI_API_BASE = "https://api.wenwen-ai.com/v1"
OPENAI_CHAT_API_KEY = "sk-Er3wXpTcIsHsrtpJSSiIkyxTgVg3ydhZ6TeTVojo5tuqKUp0"
OPENAI_CHAT_MODEL = "gpt-4o-mini"
# 非gpt大模型相关配置(oneapi方案 通义千问为例) 根据自己的实际情况进行调整
ONEAPI_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
ONEAPI_CHAT_API_KEY = "sk-d54d73979a354d7e8be0c30d494debaa"
ONEAPI_CHAT_MODEL = "qwen-plus"
# 本地大模型相关配置(Ollama方案 llama3.1:latest为例) 根据自己的实际情况进行调整
OLLAMA_API_BASE = "http://192.168.2.9:11434/v1"
OLLAMA_CHAT_API_KEY = ""
OLLAMA_CHAT_MODEL = "llama3.1:latest"


# 初始化LLM模型
model = None
# API服务设置相关  根据自己的实际情况进行调整
PORT = 3222  # 服务访问的端口
# openai:调用gpt大模型;oneapi:调用非gpt大模型;ollama:调用本地大模型
MODEL_TYPE = "oneapi"



# 定义Message类
class Message(BaseModel):
    role: str
    content: str
# 定义ChatCompletionRequest类
class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    stream: Optional[bool] = False
# 定义ChatCompletionResponseChoice类
class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = None
# 定义ChatCompletionResponse类
class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    choices: List[ChatCompletionResponseChoice]
    system_fingerprint: Optional[str] = None


# 定义了一个异步函数lifespan，它接收一个FastAPI应用实例app作为参数。这个函数将管理应用的生命周期，包括启动和关闭时的操作
# 函数在应用启动时执行一些初始化操作
# 函数在应用关闭时执行一些清理操作
# @asynccontextmanager 装饰器用于创建一个异步上下文管理器，它允许在yield之前和之后执行特定的代码块，分别表示启动和关闭时的操作
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    # 申明引用全局变量，在函数中被初始化，并在整个应用中使用
    global MODEL_TYPE, model
    global ONEAPI_API_BASE, ONEAPI_CHAT_API_KEY, ONEAPI_CHAT_MODEL
    global OPENAI_API_BASE, OPENAI_CHAT_API_KEY, OPENAI_CHAT_MODEL
    global OLLAMA_API_BASE, OLLAMA_CHAT_API_KEY, OLLAMA_CHAT_MODEL
    # 根据自己实际情况选择调用model和embedding模型类型
    try:
        print("正在初始化模型")
        # 根据MODEL_TYPE选择初始化对应的模型,默认使用gpt大模型
        if MODEL_TYPE == "oneapi":
            # 实例化一个oneapi客户端对象
            model = ChatOpenAI(
                base_url=ONEAPI_API_BASE,
                api_key=ONEAPI_CHAT_API_KEY,
                model=ONEAPI_CHAT_MODEL,  # 本次使用的模型
                temperature=0.7,# 发散的程度
                # timeout=None,# 服务请求超时
                # max_retries=2,# 失败重试最大次数
            )
        elif MODEL_TYPE == "ollama":
            # 实例化一个ChatOpenAI客户端对象
            os.environ["OPENAI_API_KEY"] = "NA"
            model = ChatOpenAI(
                base_url=OLLAMA_API_BASE,# 请求的API服务地址
                api_key=OLLAMA_CHAT_API_KEY,# API Key
                model=OLLAMA_CHAT_MODEL,# 本次使用的模型
                temperature=0.7,# 发散的程度
                # timeout=None,# 服务请求超时
                # max_retries=2,# 失败重试最大次数
            )
        else:
            # 实例化一个ChatOpenAI客户端对象
            model = ChatOpenAI(
                base_url=OPENAI_API_BASE,# 请求的API服务地址
                api_key=OPENAI_CHAT_API_KEY,# API Key
                model=OPENAI_CHAT_MODEL,# 本次使用的模型
                # temperature=0.7,# 发散的程度，一般为0
                # timeout=None,# 服务请求超时
                # max_retries=2,# 失败重试最大次数
            )

        print("LLM初始化完成")

    except Exception as e:
        print(f"初始化过程中出错: {str(e)}")
        # raise 关键字重新抛出异常，以确保程序不会在错误状态下继续运行
        raise

    # yield 关键字将控制权交还给FastAPI框架，使应用开始运行
    # 分隔了启动和关闭的逻辑。在yield 之前的代码在应用启动时运行，yield 之后的代码在应用关闭时运行
    yield
    # 关闭时执行
    print("正在关闭...")


# lifespan 参数用于在应用程序生命周期的开始和结束时执行一些初始化或清理工作
app = FastAPI(lifespan=lifespan)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# 提供前端入口
@app.get("/")
async def root():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "前端文件未找到，请确保frontend目录存在且包含index.html文件"}


# POST请求接口，与大模型进行知识问答
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    # 声明使用全局变量model，在lifespan函数中初始化
    global model
    # 如果model没有初始化，返回错误
    if model is None:
        raise HTTPException(status_code=500, detail="模型未初始化")
    
    # 从请求中提取messages
    messages = request.messages
    # 提取用户的最后一条消息作为查询
    user_query = messages[-1].content if messages else ""
    
    # 生成回复
    try:
        # 创建Crew实例并运行任务
        crew_instance = CrewtestprojectCrew(model)
        
        # 运行crew，传入用户查询作为topic参数
        result = await asyncio.to_thread(
            crew_instance.crew().kickoff, 
            inputs={"topic": user_query}
        )
        
        # 处理结果
        response_content = str(result)
        
        # 确保只处理PDF相关的保存信息
        if "PDF 保存成功" in response_content:
            # 尝试提取文件名
            import re
            filename_match = re.search(r'文件路径：(.*?)[\\/]output[\\/](.*?)$', response_content, re.MULTILINE)
            if not filename_match:
                # 尝试另一种格式
                filename_match = re.search(r'output[\\/](.*?)$', response_content, re.MULTILINE)
            
            if filename_match and len(filename_match.groups()) >= 1:
                # 添加特殊标记，方便前端识别PDF文件名
                pdf_filename = filename_match.group(len(filename_match.groups()))
                response_content += f"\n[PDF_FILENAME:{pdf_filename}]"
        
        # 非流式输出
        chat_response = ChatCompletionResponse(
            choices=[ChatCompletionResponseChoice(
                index=0,
                message=Message(role="assistant", content=response_content),
                finish_reason="stop"
            )]
        )
        # 返回JSON响应
        return chat_response
    except Exception as e:
        # 添加详细的错误日志
        error_message = f"处理请求时出错: {str(e)}"
        print(error_message)
        # 返回用户友好的错误信息，同时保持原始的异常日志
        raise HTTPException(status_code=500, detail=error_message)

@app.get("/download-pdf/{filename}")
async def download_pdf(filename: str):
    """下载生成的PDF报告"""
    pdf_path = os.path.join("output", filename)
    if os.path.exists(pdf_path):
        return FileResponse(pdf_path, media_type="application/pdf", filename=filename)
    raise HTTPException(status_code=404, detail="PDF文件未找到")



if __name__ == "__main__":
    print(f"在端口 {PORT} 上启动服务器")
    # uvicorn是一个用于运行ASGI应用的轻量级、超快速的ASGI服务器实现
    # 用于部署基于FastAPI框架的异步PythonWeb应用程序
    uvicorn.run(app, host="0.0.0.0", port=PORT)



