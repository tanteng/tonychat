from typing import AsyncGenerator, Optional, List, Dict
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from infrastructure.llm.langchain_adapter import LangChainAdapter, get_llm_adapter
from infrastructure.vectorstore.faiss_store import VectorStore, get_vector_store
from infrastructure.persistence.database import get_database
from application.services.document_service import get_document_service


RAG_PROMPT_TEMPLATE = """你是一个专业的文档问答助手。请基于以下检索到的文档内容回答用户的问题。

检索到的文档内容:
{context}

历史对话:
{history}

用户问题: {question}

请根据检索到的文档内容和历史对话回答问题。如果文档中没有相关信息，请说明"根据当前上传的文档，我无法找到相关信息来回答您的问题"。

回答要求:
1. 如果找到了相关信息，请详细引用文档内容进行回答
2. 如果需要，可以引用多个文档的内容
3. 保持回答的准确性和相关性
4. 如果文档内容确实不相关，请如实说明
5. 如果历史对话中有相关上下文，请结合考虑
"""


class ChatService:
    """Service for RAG-based chat with conversation history"""

    def __init__(
        self,
        llm_adapter: Optional[LangChainAdapter] = None,
        vector_store: Optional[VectorStore] = None
    ):
        self.llm_adapter = llm_adapter or get_llm_adapter()
        self.vector_store = vector_store or get_vector_store()

    def _get_history_string(self, session_id: str = "default") -> str:
        """Get formatted history string for a session"""
        db = get_database()
        messages = db.get_conversation_history(session_id, limit=20)
        if not messages:
            return "（无历史对话）"

        history_parts = []
        for msg in messages[-10:]:  # Keep last 10 messages
            if msg.role == 'user':
                history_parts.append(f"用户: {msg.content}")
            else:
                history_parts.append(f"助手: {msg.content}")

        return "\n".join(history_parts)

    def _add_to_history(self, session_id: str, role: str, content: str):
        """Add a message to conversation history"""
        db = get_database()
        db.add_message(session_id, role, content)

    async def chat(self, question: str, session_id: str = "default", top_k: int = 5) -> AsyncGenerator[str, None]:
        """Process a chat question with RAG and conversation history (async streaming)"""

        # Get list of valid (existing) files
        doc_service = get_document_service()
        existing_files = [doc.filename for doc in doc_service.get_all_documents()]

        # Step 1: Retrieve relevant documents from only existing files
        retrieved_docs = self.vector_store.similarity_search(
            question, k=top_k, valid_files=existing_files
        )

        # Step 2: Get context from retrieved documents
        context = self.llm_adapter.get_relevant_context(retrieved_docs)

        # Step 3: Get conversation history
        history_str = self._get_history_string(session_id)

        # Step 4: Create chain with history
        chain = self.llm_adapter.create_chat_chain_with_history(RAG_PROMPT_TEMPLATE)

        # Collect full response for history
        full_response = ""

        async for chunk in self.llm_adapter.stream(chain, {
            "context": context,
            "history": history_str,
            "question": question
        }):
            full_response += chunk
            yield chunk

        # Step 5: Save to history
        self._add_to_history(session_id, "user", question)
        self._add_to_history(session_id, "assistant", full_response)

        # Step 6: 异步生成标题（不阻塞响应）
        import threading
        thread = threading.Thread(target=self._generate_title_async, args=(session_id,))
        thread.daemon = True
        thread.start()

    def chat_sync(self, question: str, session_id: str = "default", top_k: int = 5) -> str:
        """Process a chat question with RAG and conversation history (synchronous)"""

        # Get list of valid (existing) files
        doc_service = get_document_service()
        existing_files = [doc.filename for doc in doc_service.get_all_documents()]

        # Step 1: Retrieve relevant documents from only existing files
        retrieved_docs = self.vector_store.similarity_search(
            question, k=top_k, valid_files=existing_files
        )

        # Step 2: Get context from retrieved documents
        context = self.llm_adapter.get_relevant_context(retrieved_docs)

        # Step 3: Get conversation history
        history_str = self._get_history_string(session_id)

        # Step 4: Create chain with history
        chain = self.llm_adapter.create_chat_chain_with_history(RAG_PROMPT_TEMPLATE)

        # Step 5: Get response
        response = self.llm_adapter.invoke(chain, {
            "context": context,
            "history": history_str,
            "question": question
        })

        # Step 6: Save to history
        self._add_to_history(session_id, "user", question)
        self._add_to_history(session_id, "assistant", response)

        # Step 7: 异步生成标题（不阻塞响应）
        db = get_database()
        session = db.get_session(session_id)
        if session and session.title == '新会话':
            # 只在首轮对话后生成（刚好2条消息）
            messages = db.get_conversation_history(session_id, limit=10)
            if len(messages) == 2:  # 1 user + 1 assistant
                import threading
                thread = threading.Thread(target=self._generate_title_async, args=(session_id,))
                thread.daemon = True
                thread.start()

        return response

    def chat_stream(self, question: str, session_id: str = "default", top_k: int = 5, timeout: float = 60.0):
        """Process a chat question with real streaming using httpx directly"""
        import httpx
        import os
        import json
        import threading
        import queue

        # Get list of valid (existing) files
        doc_service = get_document_service()
        existing_files = [doc.filename for doc in doc_service.get_all_documents()]

        # Step 1: Retrieve relevant documents
        retrieved_docs = self.vector_store.similarity_search(
            question, k=top_k, valid_files=existing_files
        )

        # Step 2: Get context
        context = self.llm_adapter.get_relevant_context(retrieved_docs)

        # Step 3: Get conversation history
        history_str = self._get_history_string(session_id)

        # Step 4: Prepare messages for API call
        messages = [
            {"role": "system", "content": RAG_PROMPT_TEMPLATE},
            {"role": "user", "content": f"上下文：{context}\n\n历史：{history_str}\n\n问题：{question}"}
        ]

        # Step 5: Stream using httpx directly
        api_key = os.environ.get('OPENAI_API_KEY', '')
        base_url = os.environ.get('OPENAI_API_BASE', 'https://api.siliconflow.cn/v1')
        model = os.environ.get('LLM_MODEL', 'deepseek-ai/DeepSeek-V3.2')

        chunk_queue = queue.Queue()
        error_holder = [None]

        def stream_response():
            try:
                with httpx.stream(
                    "POST",
                    f"{base_url}/chat/completions",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": True,
                        "temperature": self.llm_adapter.temperature,
                    },
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=httpx.Timeout(timeout, read=timeout),
                ) as response:
                    for line in response.iter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(data)
                            delta = chunk_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if delta:
                                chunk_queue.put(delta)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                error_holder[0] = e
            finally:
                chunk_queue.put(None)  # Signal completion

        thread = threading.Thread(target=stream_response)
        thread.start()

        # Yield chunks as they come
        full_response = ""
        while True:
            try:
                chunk = chunk_queue.get(timeout=timeout)
                if chunk is None:  # Stream ended
                    break
                full_response += chunk
                yield chunk
            except queue.Empty:
                raise TimeoutError(f"LLM streaming timed out after {timeout} seconds")

        thread.join(timeout=5)
        if error_holder[0]:
            raise error_holder[0]

        # Step 6: Save to history (after streaming completes)
        self._add_to_history(session_id, "user", question)
        self._add_to_history(session_id, "assistant", full_response)

        # Step 7: 异步生成标题
        db = get_database()
        session = db.get_session(session_id)
        if session and session.title == '新会话':
            messages = db.get_conversation_history(session_id, limit=10)
            if len(messages) == 2:
                thread = threading.Thread(target=self._generate_title_async, args=(session_id,))
                thread.daemon = True
                thread.start()

    def _generate_title_async(self, session_id: str):
        """异步生成会话标题（在线程中运行）"""
        try:
            title = self.generate_session_title(session_id)
            print(f"[标题生成] session={session_id}, title={title}")
        except Exception as e:
            print(f"[标题生成] 失败: {e}")

    def generate_session_title(self, session_id: str) -> str:
        """使用 LLM 生成会话标题"""
        db = get_database()
        messages = db.get_conversation_history(session_id, limit=4)

        if len(messages) < 2:
            return "新会话"

        # 取前两条消息
        context_parts = []
        for msg in messages[:2]:
            if msg.role == 'user':
                context_parts.append(f"用户问题: {msg.content[:100]}")
            elif msg.role == 'assistant':
                context_parts.append(f"助手回答: {msg.content[:100]}")

        context_text = "\n".join(context_parts)

        title_prompt = f"""根据以下对话生成一个简短的中文会话标题（最多20字）：

{context_text}

标题："""

        try:
            # 使用专门的 Qwen 模型生成标题
            from langchain_core.output_parsers import StrOutputParser
            from langchain_core.prompts import ChatPromptTemplate
            from infrastructure.llm.langchain_adapter import get_title_llm

            title_llm = get_title_llm()
            prompt = ChatPromptTemplate.from_template("{text}")
            chain = prompt | title_llm | StrOutputParser()
            title = chain.invoke({"text": title_prompt})
            title = title.strip()[:20]
            if not title:
                title = "新会话"
            db.update_session_title(session_id, title)
            return title
        except Exception as e:
            print(f"生成标题失败: {e}")
            return "新会话"

    def clear_history(self, session_id: str = "default"):
        """Clear conversation history for a session"""
        db = get_database()
        db.clear_conversation_history(session_id)

    def get_retrieved_context(self, question: str, top_k: int = 5) -> tuple[str, list[Document]]:
        """Get the retrieved context for debugging"""
        retrieved_docs = self.vector_store.similarity_search(question, k=top_k)
        context = self.llm_adapter.get_relevant_context(retrieved_docs)
        return context, retrieved_docs


# Global singleton instance
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
