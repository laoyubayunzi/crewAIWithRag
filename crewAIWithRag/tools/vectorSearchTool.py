# 引入相关库
from crewai_tools import tool
import logging
from openai import OpenAI
import chromadb
import uuid
import numpy as np
import traceback

# 设置日志模版
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 模型设置相关 - 根据实际情况调整
API_TYPE = "oneapi"  # openai:调用gpt模型；oneapi:调用通义千问（阿里云百炼）
# openai模型相关配置
OPENAI_API_BASE = "https://api.wlai.vip/v1"
OPENAI_EMBEDDING_API_KEY = "sk-d54d73979a354d7e8be0c30d494debaa"
OPENAI_EMBEDDING_MODEL = "qwen-plus"
# oneapi相关配置（通义千问，阿里云百炼兼容模式）
ONEAPI_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
ONEAPI_EMBEDDING_API_KEY = "sk-d54d73979a354d7e8be0c30d494debaa"
ONEAPI_EMBEDDING_MODEL = "text-embedding-v2"  # 通义千问嵌入模型（非对话模型）
# 向量数据库配置（Windows 路径，项目内相对路径）
CHROMADB_DIRECTORY = r"F:\浏览器下载\crewAIWithRag\chromaDB"  # 自动创建文件夹
CHROMADB_COLLECTION_NAME = "demo001"  # 向量集合名称


# -------------------------- 核心修正 1：修复向量生成格式（返回二维列表） --------------------------
def get_embeddings(texts):
    global API_TYPE, ONEAPI_API_BASE, ONEAPI_EMBEDDING_API_KEY, ONEAPI_EMBEDDING_MODEL
    global OPENAI_API_BASE, OPENAI_EMBEDDING_API_KEY, OPENAI_EMBEDDING_MODEL

    if API_TYPE == 'oneapi':
        try:
            client = OpenAI(base_url=ONEAPI_API_BASE, api_key=ONEAPI_EMBEDDING_API_KEY)
            data = client.embeddings.create(input=texts, model=ONEAPI_EMBEDDING_MODEL).data
            return [x.embedding for x in data]  # 二维列表：[[vec1], [vec2]]
        except Exception as e:
            logger.error(f"oneapi 生成向量失败：{str(e)}\n{traceback.format_exc()}")
            return []
    elif API_TYPE == 'openai':
        try:
            client = OpenAI(base_url=OPENAI_API_BASE, api_key=OPENAI_EMBEDDING_API_KEY)
            data = client.embeddings.create(input=texts, model=OPENAI_EMBEDDING_MODEL).data
            return [x.embedding for x in data]
        except Exception as e:
            logger.error(f"openai 生成向量失败：{str(e)}\n{traceback.format_exc()}")
            return []


# 按批次生成向量（修复为二维列表）
def generate_vectors(data, max_batch_size=25):
    results = []
    for i in range(0, len(data), max_batch_size):
        batch = data[i:i + max_batch_size]
        response = get_embeddings(batch)
        if response:
            results.append(response)  # 保留二维结构
    return [vec for batch_vecs in results for vec in batch_vecs]  # 展平为 [[vec1], [vec2]]


# -------------------------- 向量数据库封装（增加异常处理） --------------------------
class MyVectorDBConnector:
    def __init__(self, collection_name, embedding_fn):
        global CHROMADB_DIRECTORY
        self.collection = None
        try:
            chroma_client = chromadb.PersistentClient(path=CHROMADB_DIRECTORY)
            self.collection = chroma_client.get_or_create_collection(name=collection_name)
            self.embedding_fn = embedding_fn
            logger.info(f"向量数据库初始化成功：{CHROMADB_DIRECTORY}/{collection_name}")
        except Exception as e:
            logger.error(f"向量数据库初始化失败：{str(e)}\n{traceback.format_exc()}")

    # 检索向量数据库
    def search(self, query, top_n):
        if not self.collection:
            logger.error("向量数据库未初始化")
            return {}
        try:
            query_embeds = self.embedding_fn([query])
            if not query_embeds:
                logger.error("查询向量生成失败")
                return {}
            results = self.collection.query(query_embeddings=query_embeds, n_results=top_n)
            logger.info(f"检索到 {len(results.get('documents', [[]])[0])} 条结果")
            return results
        except Exception as e:
            logger.error(f"检索失败：{str(e)}\n{traceback.format_exc()}")
            return {}


# -------------------------- 核心修正 2：工具函数接收字典参数（适配老版本 crewai_tools） --------------------------
@tool("vectorSearch")  # 去掉 model 参数，兼容老版本
def vectorSearch(inputs: dict) -> str:  # 直接接收字典参数
    """
    使用这个工具来完成根据用户的问题，从健康档案库中检索相关的内容。
    :param inputs: 字典格式，必须包含 "user_query" 键（值为用户问题字符串）
    :return: 检索结果字符串
    """
    global CHROMADB_COLLECTION_NAME
    # 从字典中提取 user_query（兼容 crewai 调用格式）
    user_query = inputs.get("user_query", "").strip()
    if not user_query:
        return "未获取到有效的用户问题，请重新输入。"

    try:
        vector_db = MyVectorDBConnector(CHROMADB_COLLECTION_NAME, generate_vectors)
        search_results = vector_db.search(user_query, 2)

        # 安全处理结果，避免索引错误
        documents = search_results.get("documents", [[]])
        if not isinstance(documents, list) or len(documents) == 0 or not documents[0]:
            return f"未检索到与「{user_query}」相关的健康档案记录。"

        full_text = "\n".join([doc.strip() for doc in documents[0] if doc.strip()])
        return f"检索到与「{user_query}」相关的健康档案结果：\n{full_text}"

    except Exception as e:
        error_msg = f"检索健康档案时发生错误：{str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return error_msg


# -------------------------- 测试代码（模拟 crewai 调用格式） --------------------------
if __name__ == "__main__":
    # 模拟 crewai 传入的字典格式
    test_input = {"user_query": "我嗓子疼"}
    test_result = vectorSearch(test_input)  # 直接传字典，无需实例化
    print("工具测试结果：")
    print(test_result)