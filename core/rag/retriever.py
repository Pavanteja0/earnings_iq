import re
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from .indexer import Indexer

class Retriever:
    """
    Retrieves and reranks document chunks relevant to analyst queries.
    Implements metadata-aware search and LLM-based reranking.
    """
    def __init__(self, indexer: Indexer):
        self.indexer = indexer
        self.collection = indexer.collection

    def retrieve(
        self, 
        query: str, 
        top_k: int = 5, 
        source_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top_k chunks for a query.
        source_type can be: '10-Q', 'Slide Deck', 'Transcript File', or None.
        """
        # Formulate metadata filter if specified
        where_filter = {}
        if source_type:
            where_filter = {"type": source_type}

        # Query ChromaDB (returns top 15 candidates for reranking)
        candidate_k = max(top_k * 3, 15)
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=candidate_k,
                where=where_filter if where_filter else None
            )
        except Exception as e:
            print(f"Retrieval error: {e}")
            return []

        if not results or not results["documents"] or not results["documents"][0]:
            return []

        # Parse ChromaDB output into structured chunks
        candidate_chunks = []
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(documents)
        ids = results["ids"][0]

        for doc, meta, dist, cid in zip(documents, metadatas, distances, ids):
            candidate_chunks.append({
                "id": cid,
                "text": doc,
                "metadata": meta,
                "distance": dist,
                "relevance_score": 1.0 - dist  # Convert distance to similarity score
            })

        # Apply LLM Reranking if Gemini API is available
        is_gemini_active = self.indexer.embedding_fn.is_active
        if is_gemini_active and len(candidate_chunks) > 1:
            try:
                reranked_chunks = self._llm_rerank(query, candidate_chunks, top_k)
                return reranked_chunks
            except Exception as e:
                print(f"LLM Reranking failed: {e}. Falling back to default cosine ranking.")
        
        # Fallback: Sort by cosine similarity score and take top_k
        candidate_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
        return candidate_chunks[:top_k]

    def _llm_rerank(
        self, 
        query: str, 
        chunks: List[Dict[str, Any]], 
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Uses Gemini to score and rerank chunks based on relevance to the query.
        """
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Build prompt listing the candidate chunks
        prompt = (
            f"You are a financial research auditor. We are searching for answers to the query: '{query}'\n"
            f"Rate the relevance of each of the following text passages on a scale of 0 to 10, "
            f"where 10 means the passage contains the exact direct answer or critical numbers, and 0 means irrelevant.\n"
            f"Provide your scores in a simple comma-separated list of values, corresponding to the passage IDs in order. "
            f"Format like: [ID1: Score1, ID2: Score2, ...]\n\n"
        )
        
        for idx, chunk in enumerate(chunks):
            prompt += f"--- PASSAGE {idx} (ID: {chunk['id']}) ---\n{chunk['text']}\n\n"

        response = model.generate_content(prompt)
        response_text = response.text
        
        # Extract scores using regex
        scores = {}
        # Look for patterns like chunk_xxxx_xxxx: 8 or chunk_xxxx_xxxx - 8 or ID: 8
        score_matches = re.findall(r"([a-zA-Z0-9_\-]+)\s*[:\-]\s*(\d+)", response_text)
        
        for cid, score_str in score_matches:
            try:
                scores[cid.strip()] = int(score_str.strip())
            except ValueError:
                pass
                
        # Assign scores to chunks
        for chunk in chunks:
            chunk["rerank_score"] = scores.get(chunk["id"], 5)  # Default score 5 if parsing failed
            # Combined score: 70% LLM rerank score, 30% vector similarity score
            chunk["final_score"] = (chunk["rerank_score"] / 10.0) * 0.7 + chunk["relevance_score"] * 0.3

        # Sort by final score
        chunks.sort(key=lambda x: x.get("final_score", x["relevance_score"]), reverse=True)
        return chunks[:top_k]
