# 健康档案助手智能体

## 项目简介
这是一个基于CrewAI框架开发的健康档案助手智能体系统，通过两个专业Agent的协作，实现健康问题的智能分析与报告生成。系统采用检索增强生成(RAG)技术，能够从健康档案向量数据库中检索相关信息，并生成专业的健康建议报告。

## 核心功能

1. **健康档案智能检索**
   - 基于用户提出的健康问题，从向量数据库中精确检索相关健康档案记录
   - 支持语义理解，即使问题表述不同也能找到相关内容

2. **专业健康报告生成**
   - 根据检索结果和用户问题，生成包含医学依据的健康建议报告
   - 报告内容包括健康状况分析和个性化改善建议

3. **PDF文件自动导出**
   - 支持将健康报告自动保存为PDF格式文件
   - 内置中文支持，无需额外字体文件配置

4. **多模型支持**
   - 兼容多种大语言模型：OpenAI GPT、通义千问(OneAPI)、本地Ollama模型
   - 可根据需要灵活切换不同模型

5. **Web界面交互**
   - 提供用户友好的Web界面进行健康问题咨询
   - 支持历史记录查看和PDF报告下载

## 系统架构

### 1. 智能体设计

- **健康档案检索专家(Retrieval Agent)**
  - 角色：专业健康档案检索专家
  - 目标：根据用户健康问题，从健康档案库中检索相关记录
  - 工具：向量检索工具(vectorSearch)

- **健康报告撰写专家(Report Agent)**
  - 角色：医学背景的报告撰写专家
  - 目标：分析检索结果，撰写专业健康建议报告
  - 工具：PDF生成工具(saveText2Pdf)

### 2. 工作流程

1. 用户通过Web界面提交健康问题
2. FastAPI后端接收请求并传递给CrewAI系统
3. 检索专家使用向量检索工具查询相关健康档案
4. 报告专家根据检索结果和问题撰写健康建议报告
5. 自动生成PDF格式报告并保存到本地
6. 返回报告结果和下载链接给用户

### 3. 技术栈

- **后端框架**：FastAPI、Python 3.x
- **智能体框架**：CrewAI
- **向量数据库**：ChromaDB
- **大模型接口**：OpenAI API、OneAPI、Ollama
- **前端技术**：HTML、Tailwind CSS、JavaScript
- **PDF生成**：FPDF、PIL (Python Imaging Library)


## 安装与配置

### 1. 环境准备

```bash
# 克隆项目后进入目录
cd crewAIWithRag

# 安装依赖
pip install -r requirements.txt
```

### 2. 模型配置

在`main.py`文件中配置您使用的大语言模型参数：

- **OpenAI模型**：配置API_BASE、API_KEY和MODEL
- **通义千问模型**：配置ONEAPI相关参数
- **本地Ollama模型**：配置OLLAMA相关参数
- **选择模型类型**：设置MODEL_TYPE为"openai"、"oneapi"或"ollama"

### 3. 向量数据库配置

在`tools/vectorSearchTool.py`中配置向量数据库参数：

- **CHROMADB_DIRECTORY**：向量数据库存储路径
- **CHROMADB_COLLECTION_NAME**：向量集合名称
- **嵌入模型配置**：根据API_TYPE选择对应的嵌入模型参数

## 使用方法

### 1. 启动服务

```bash
# 直接运行main.py
python main.py
```

服务将在配置的端口(默认3222)上启动，可通过浏览器访问：http://localhost:3222

### 2. API调用示例

系统提供标准的OpenAI兼容API接口：

```bash
# 使用curl调用API示例
curl -X POST "http://localhost:3222/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "心脏病有哪些预防措施？"}], "stream": false}'
```

### 3. PDF报告下载

系统生成报告后，可通过返回的链接下载PDF文件：

```
http://localhost:3222/download-pdf/[报告文件名].pdf
```

## 关键实现细节

### 1. 向量检索实现

系统使用ChromaDB作为向量存储，通过嵌入模型将用户问题和健康档案文本转换为向量表示，然后进行相似度搜索。向量检索工具(`vectorSearchTool.py`)支持按批次处理，提高检索效率。

### 2. PDF生成机制

PDF生成工具(`savePdfTool.py`)通过创新的图片转文字方式解决中文显示问题，无需依赖特定中文字体文件。实现步骤：

1. 将文本内容渲染为图片
2. 自动处理中文换行和排版
3. 使用多种字体回退机制确保中文正常显示
4. 将图片插入PDF并保存

### 3. 智能体协作流程

系统采用顺序执行(Sequential)流程，确保两个Agent按特定顺序协作：

1. 检索Agent先完成相关健康档案的搜索
2. 搜索结果自动传递给报告Agent
3. 报告Agent基于检索内容生成专业健康建议
4. 最终输出结构化的健康报告并保存为PDF

## 注意事项

1. 请确保正确配置模型API密钥和参数，否则可能导致服务启动失败
2. 首次运行时，确保`chromaDB`目录有写入权限以创建向量数据库
3. 系统默认将生成的PDF报告保存在`output`目录下
4. 如需修改服务端口，请在`main.py`中调整`PORT`参数

## 开发说明

- 系统使用CrewAI的装饰器模式定义Agent和Task，配置与代码分离
- 支持自定义工具扩展，可根据需要添加新的功能模块
- 提供完整的错误处理和日志记录，便于调试和问题排查

## 许可证

本项目仅供学习和研究使用。