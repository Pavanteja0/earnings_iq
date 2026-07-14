import uuid
import chromadb
from pathlib import Path
from typing import List, Dict, Any
import google.generativeai as genai
from chromadb.api.types import Documents, Embeddings

from config import DB_DIR, EMBEDDING_MODEL

class GeminiEmbeddingFunction(chromadb.EmbeddingFunction):
    """
    Custom embedding function for ChromaDB that calls the Gemini Embedding API.
    If Gemini is not active or fails, it falls back to a deterministic dummy embedding 
    suitable for testing without breaking the flow.
    """
    def __init__(self, is_active: bool = False):
        self.is_active = is_active

    def __call__(self, input: Documents) -> Embeddings:
        if self.is_active:
            try:
                # Call Gemini embedding API
                response = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=input,
                    task_type="retrieval_document"
                )
                return response["embedding"]
            except Exception as e:
                print(f"Error generating Gemini embeddings: {e}. Falling back to mockup.")
        
        # Fallback dummy embeddings: generate a list of floats based on string length and hashing
        embeddings = []
        for text in input:
            # Create a mock vector of 768 dimensions
            val = sum(ord(c) for c in text[:100]) % 100 / 100.0
            vector = [val * (i / 768.0) for i in range(768)]
            embeddings.append(vector)
        return embeddings

    @staticmethod
    def name() -> str:
        return "GeminiEmbeddingFunction"

    def get_config(self) -> Dict[str, Any]:
        return {"is_active": self.is_active}

    @staticmethod
    def build_from_config(config: Dict[str, Any]) -> "GeminiEmbeddingFunction":
        return GeminiEmbeddingFunction(is_active=config.get("is_active", False))


class Indexer:
    """
    Handles indexing of document chunks into ChromaDB.
    """
    def __init__(self):
        # Initialize persistent Chroma client
        self.client = chromadb.PersistentClient(path=str(DB_DIR))
        
        # Check if Gemini API is active
        from config import is_gemini_api_active
        is_gemini_active = is_gemini_api_active()

        self.embedding_fn = GeminiEmbeddingFunction(is_active=is_gemini_active)
        
        # Create or retrieve collection
        self.collection = self.client.get_or_create_collection(
            name="earnings_reports",
            embedding_function=self.embedding_fn
        )

    def reset_collection(self):
        """Resets the collection by deleting and recreating it."""
        try:
            self.client.delete_collection("earnings_reports")
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name="earnings_reports",
            embedding_function=self.embedding_fn
        )

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Adds parsed document chunks to the database.
        Each chunk is expected to be a dictionary:
        {
            "text": str,
            "metadata": dict
        }
        """
        if not chunks:
            return

        documents = []
        metadatas = []
        ids = []

        for idx, chunk in enumerate(chunks):
            documents.append(chunk["text"])
            
            # ChromaDB only supports string, int, float, or bool in metadata
            # Flatten/sanitize metadata just in case
            metadata = {}
            for k, v in chunk["metadata"].items():
                if isinstance(v, (str, int, float, bool)):
                    metadata[k] = v
                else:
                    metadata[k] = str(v)
            metadatas.append(metadata)
            
            # Generate unique ID
            chunk_id = f"chunk_{metadata.get('type', 'doc')}_{uuid.uuid4().hex[:10]}_{idx}"
            ids.append(chunk_id)

        # Add in batches to avoid size limits
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            self.collection.add(
                documents=documents[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
                ids=ids[i : i + batch_size]
            )
            
        print(f"Successfully indexed {len(documents)} chunks to ChromaDB.")

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics about the indexed documents."""
        count = self.collection.count()
        return {
            "total_chunks": count,
        }
