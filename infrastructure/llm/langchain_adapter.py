import os
from typing import AsyncGenerator, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


class LangChainAdapter:
    """LangChain adapter for LLM calls"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float = 0.7
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self._llm: Optional[ChatOpenAI] = None
        self._title_llm: Optional[ChatOpenAI] = None

    @property
    def llm(self) -> ChatOpenAI:
        if self._llm is None:
            self._llm = ChatOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model,
                temperature=self.temperature,
                streaming=True
            )
        return self._llm

    @property
    def title_llm(self) -> ChatOpenAI:
        """轻量级 LLM 用于生成标题（Qwen2.5-7B）"""
        if self._title_llm is None:
            self._title_llm = ChatOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                model=os.environ.get('TITLE_MODEL', 'Qwen/Qwen2.5-7B-Instruct'),
                temperature=0.3,  # 标题生成用低温
                streaming=False
            )
        return self._title_llm

    def create_chat_chain(self, prompt_template: str):
        """Create a chat chain with the given prompt template"""
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        return chain

    def create_chat_chain_with_history(self, prompt_template: str):
        """Create a chat chain that includes conversation history"""
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        return chain

    async def stream(self, chain, input_data: dict) -> AsyncGenerator[str, None]:
        """Stream response from chain"""
        async for chunk in chain.astream(input_data):
            yield chunk

    def invoke(self, chain, input_data: dict) -> str:
        """Invoke chain and return full response (non-streaming)"""
        return chain.invoke(input_data)

    def get_relevant_context(self, docs) -> str:
        """Format retrieved documents as context string with source info"""
        if not docs:
            return "（没有找到相关文档内容）"

        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "未知文档")
            # 提取文件名（去掉路径）
            filename = source.split('/')[-1] if '/' in source else source
            context_parts.append(f"【引用 {i}】文件名：{filename}\n{doc.page_content}")

        return "\n\n".join(context_parts)


# Global singleton instance
_llm_adapter: Optional[LangChainAdapter] = None


def get_llm_adapter() -> LangChainAdapter:
    global _llm_adapter
    if _llm_adapter is None:
        # Lazy load env vars to ensure dotenv is loaded first
        from dotenv import load_dotenv
        load_dotenv()

        _llm_adapter = LangChainAdapter(
            api_key=os.environ.get('OPENAI_API_KEY', ''),
            base_url=os.environ.get('OPENAI_API_BASE', 'https://api.siliconflow.cn/v1'),
            model=os.environ.get('LLM_MODEL', 'deepseek-ai/DeepSeek-V3.2')
        )
    return _llm_adapter


def get_title_llm() -> ChatOpenAI:
    """获取专门用于标题生成的轻量级 LLM"""
    adapter = get_llm_adapter()
    return adapter.title_llm
