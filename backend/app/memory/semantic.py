from typing import Optional, List, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from openai import AsyncOpenAI
from app.config import settings
from app.utils.logger import logger
import uuid


class SemanticMemory:
    """
    ChromaDB-backed vector memory for semantic similarity search.
    Stores facts, knowledge, and conversation summaries as embeddings.
    Enables the agent to recall relevant past knowledge given a query.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.collection_name = f"{settings.chroma_collection_name}_{user_id}"
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self._client: Optional[chromadb.AsyncHttpClient] = None
        self._collection = None

    async def _get_collection(self):
        if self._collection is None:
            try:
                self._client = await chromadb.AsyncHttpClient(
                    host=settings.chroma_host,
                    port=settings.chroma_port,
                )
                self._collection = await self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception:
                # Fallback to in-process ChromaDB if server unavailable
                logger.warning("chromadb_server_unavailable_using_in_process")
                self._client = chromadb.Client()
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
        return self._collection

    async def _embed(self, text: str) -> List[float]:
        if settings.fast_embeddings:
            import hashlib
            h = hashlib.sha256(text.encode('utf-8')).digest()
            res = []
            for i in range(1536):
                byte_val = h[i % len(h)]
                res.append(float(byte_val) / 255.0 - 0.5)
            return res

        try:
            model_name = "nomic-embed-text" if ("ollama" in str(settings.openai_api_key) or "11434" in str(settings.openai_base_url)) else "text-embedding-3-small"
            response = await self.openai.embeddings.create(
                model=model_name,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning("embeddings_generation_failed_using_fallback", error=str(e))
            import hashlib
            h = hashlib.sha256(text.encode('utf-8')).digest()
            res = []
            for i in range(1536):
                byte_val = h[i % len(h)]
                res.append(float(byte_val) / 255.0 - 0.5)
            return res


    async def store(
        self,
        content: str,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        collection = await self._get_collection()
        doc_id = document_id or str(uuid.uuid4())
        embedding = await self._embed(content)

        meta = {"user_id": self.user_id, **(metadata or {})}

        try:
            collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[meta],
            )
        except Exception:
            # Async collection
            await collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[meta],
            )

        logger.info("semantic_memory_stored", doc_id=doc_id)
        return doc_id

    async def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        collection = await self._get_collection()
        embedding = await self._embed(query)

        where = {"user_id": self.user_id}
        if filter_metadata:
            where.update(filter_metadata)

        try:
            results = collection.query(
                query_embeddings=[embedding],
                n_results=n_results,
                where=where,
            )
        except Exception:
            results = await collection.query(
                query_embeddings=[embedding],
                n_results=n_results,
                where=where,
            )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]

        return [
            {
                "id": ids[i],
                "content": documents[i],
                "metadata": metadatas[i],
                "similarity": 1 - distances[i],  # cosine distance → similarity
            }
            for i in range(len(documents))
        ]

    async def search_as_context(self, query: str, n_results: int = 3) -> str:
        results = await self.search(query, n_results=n_results)
        if not results:
            return ""
        lines = ["=== Relevant Memories ==="]
        for r in results:
            score = round(r["similarity"] * 100, 1)
            lines.append(f"[{score}% relevant] {r['content']}")
        return "\n".join(lines)

    async def delete(self, document_id: str):
        collection = await self._get_collection()
        try:
            collection.delete(ids=[document_id])
        except Exception:
            await collection.delete(ids=[document_id])
