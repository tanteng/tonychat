# TonyChat - AI Document Q&A Assistant

基于 RAG（检索增强生成）的智能文档问答助手，支持多会话管理和流式输出。

## 功能特性

- 📄 **文档问答** - 支持 PDF、TXT、MD、DOCX 格式上传，基于文档内容进行智能问答
- 💬 **多会话管理** - 支持创建、切换、删除会话，AI 自动生成会话标题
- ⚡ **流式输出** - AG-UI 协议支持的实时流式响应，打字机效果
- 🔍 **向量检索** - FAISS 向量数据库，支持语义相似度检索
- 📝 **会话历史** - 持久化存储对话记录，刷新页面不丢失
- 🤖 **模型支持** - 支持 OpenAI、Claude 等主流 LLM，标题生成使用 Qwen2.5-7B

## 技术栈

- **后端**: Flask + SQLAlchemy + SQLite
- **前端**: 原生 HTML/CSS/JavaScript
- **向量库**: FAISS
- **LLM**: LangChain + SiliconFlow API

## 本地部署

### 1. 克隆项目

```bash
git clone https://github.com/tanteng/tonychat.git
cd tonychat
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
.\venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API Key：

```env
# SiliconFlow API（支持 OpenAI/Claude/Qwen 等模型）
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.siliconflow.cn/v1

# LLM 模型配置
LLM_MODEL=deepseek-ai/DeepSeek-V3.2
TITLE_MODEL=Qwen/Qwen2.5-7B-Instruct
```

### 5. 启动服务

```bash
python app.py
```

访问 http://localhost:5001

## 使用方式

1. **上传文档** - 点击上传区域或拖拽文件到此处
2. **开始提问** - 在输入框输入问题，按 Enter 或点击发送
3. **会话管理** - 在侧边栏创建、切换、删除会话

## 项目结构

```
tonychat/
├── app.py                      # Flask 入口
├── api/
│   └── routes.py               # API 路由
├── application/
│   └── services/
│       ├── chat_service.py     # 聊天服务
│       └── document_service.py # 文档服务
├── infrastructure/
│   ├── llm/
│   │   └── langchain_adapter.py
│   ├── vectorstore/
│   │   └── faiss_store.py
│   └── persistence/
│       └── database.py        # 数据库
├── templates/
│   └── index.html             # 前端页面
└── uploads/                   # 上传文件目录
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 前端页面 |
| POST | `/chat` | 发送消息（支持 session_id） |
| GET | `/sessions` | 获取会话列表 |
| POST | `/sessions` | 创建会话 |
| DELETE | `/sessions/<id>` | 删除会话 |
| GET | `/sessions/<id>/messages` | 获取会话历史 |
| POST | `/upload` | 上传文档 |
| GET | `/files` | 文件列表 |
| DELETE | `/files/<filename>` | 删除文件 |

## 注意事项

- 首次使用需要上传文档才能进行问答
- 对话记录保存在 `chat.db` SQLite 数据库
- 向量索引保存在 `vectorstore.index/` 目录
- 支持的文档格式：.txt, .md, .pdf, .docx
