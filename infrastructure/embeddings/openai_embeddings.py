import os
import requests
from typing import List, Optional, Tuple
from langchain_core.embeddings import Embeddings


class SiliconFlowEmbeddings(Embeddings):
    """Custom embeddings for SiliconFlow API"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str = "BAAI/bge-m3"
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model

    def _call_api(self, texts: List[str]) -> List[List[float]]:
        """Call SiliconFlow embeddings API"""
        response = requests.post(
            f'{self.base_url}/embeddings',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': self.model,
                'input': texts
            },
            timeout=60
        )

        if response.status_code != 200:
            raise Exception(f"Embedding API error: {response.status_code} - {response.text}")

        result = response.json()
        return [item['embedding'] for item in result['data']]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts with batching"""
        all_embeddings = []
        batch_size = 64  # SiliconFlow limit

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            all_embeddings.extend(self._call_api(batch))

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        return self._call_api([text])[0]


# Global singleton instance
_embeddings_adapter: Optional['EmbeddingsAdapter'] = None


class EmbeddingsAdapter:
    """Adapter for generating embeddings"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str = "BAAI/bge-m3"
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._embeddings: Optional[SiliconFlowEmbeddings] = None

    @property
    def embeddings(self) -> SiliconFlowEmbeddings:
        if self._embeddings is None:
            self._embeddings = SiliconFlowEmbeddings(
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model
            )
        return self._embeddings


def get_embeddings_adapter() -> EmbeddingsAdapter:
    global _embeddings_adapter
    if _embeddings_adapter is None:
        from dotenv import load_dotenv
        load_dotenv()

        _embeddings_adapter = EmbeddingsAdapter(
            api_key=os.environ.get('OPENAI_API_KEY', ''),
            base_url=os.environ.get('OPENAI_API_BASE', 'https://api.siliconflow.cn/v1'),
            model=os.environ.get('EMBEDDING_MODEL', 'BAAI/bge-m3')
        )
    return _embeddings_adapter
