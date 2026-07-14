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
        Retrieves top_k chunks for a query using true Hybrid Search (Vector + BM25 keyword search)
        and LLM-based reranking.
        """
        from rank_bm25 import BM25Okapi
        
        where_filter = {}
        if source_type:
            where_filter = {"type": source_type}

        # 1. Fetch all documents matching the metadata filter to build the BM25 corpus
        try:
            all_docs = self.collection.get(
                where=where_filter if where_filter else None,
                include=["documents", "metadatas"]
            )
        except Exception as e:
            print(f"Error fetching docs for BM25: {e}")
            all_docs = None

        # Build BM25 index if documents are present
        doc_id_to_bm25 = {}
        has_bm25 = False
        if all_docs and all_docs.get("documents"):
            docs = all_docs["documents"]
            ids = all_docs["ids"]
            metas = all_docs["metadatas"]
            
            tokenized_corpus = [doc.lower().split() for doc in docs]
            try:
                bm25 = BM25Okapi(tokenized_corpus)
                tokenized_query = query.lower().split()
                bm25_scores = bm25.get_scores(tokenized_query)
                
                # Min-max scale normalization for BM25 scores
                max_b = max(bm25_scores) if len(bm25_scores) > 0 else 0.0
                min_b = min(bm25_scores) if len(bm25_scores) > 0 else 0.0
                range_b = max_b - min_b
                
                for idx, (cid, doc, meta, score) in enumerate(zip(ids, docs, metas, bm25_scores)):
                    norm_score = (score - min_b) / range_b if range_b > 0 else 0.0
                    doc_id_to_bm25[cid] = {
                        "id": cid,
                        "text": doc,
                        "metadata": meta,
                        "bm25_score": score,
                        "norm_bm25": norm_score
                    }
                has_bm25 = True
            except Exception as e:
                print(f"Failed to initialize BM25: {e}")

        # 2. Run Vector Search on ChromaDB
        candidate_k = max(top_k * 3, 15)
        vector_results = None
        try:
            vector_results = self.collection.query(
                query_texts=[query],
                n_results=min(candidate_k, len(all_docs["ids"])) if all_docs and all_docs.get("ids") else candidate_k,
                where=where_filter if where_filter else None
            )
        except Exception as e:
            print(f"Vector search query error: {e}")

        # Parse Vector Search results
        vector_candidates = {}
        if vector_results and vector_results.get("documents") and vector_results["documents"][0]:
            v_docs = vector_results["documents"][0]
            v_ids = vector_results["ids"][0]
            v_metas = vector_results["metadatas"][0]
            v_dists = vector_results["distances"][0] if "distances" in vector_results and vector_results["distances"] else [0.5] * len(v_docs)
            
            # Normalize vector scores (clamping similarity score between 0.0 and 1.0)
            max_v = max([1.0 - d for d in v_dists]) if v_dists else 1.0
            min_v = min([1.0 - d for d in v_dists]) if v_dists else 0.0
            range_v = max_v - min_v
            
            for cid, doc, meta, dist in zip(v_ids, v_docs, v_metas, v_dists):
                sim = 1.0 - dist
                norm_sim = (sim - min_v) / range_v if range_v > 0 else 0.5
                vector_candidates[cid] = {
                    "id": cid,
                    "text": doc,
                    "metadata": meta,
                    "similarity": sim,
                    "norm_vector": norm_sim
                }

        # 3. Fuse Scores (0.5 * Vector + 0.5 * BM25)
        # Combine unique document IDs retrieved by either vector or top BM25
        top_bm25_candidates = sorted(doc_id_to_bm25.values(), key=lambda x: x["norm_bm25"], reverse=True)[:candidate_k] if has_bm25 else []
        top_bm25_ids = {item["id"] for item in top_bm25_candidates}
        
        all_candidate_ids = set(vector_candidates.keys()).union(top_bm25_ids)
        fused_chunks = []
        
        for cid in all_candidate_ids:
            # Retrieve textual content from either source
            if cid in vector_candidates:
                doc_data = vector_candidates[cid]
                text = doc_data["text"]
                metadata = doc_data["metadata"]
                v_score = doc_data["norm_vector"]
            else:
                doc_data = doc_id_to_bm25[cid]
                text = doc_data["text"]
                metadata = doc_data["metadata"]
                v_score = 0.0  # assumed 0 since it wasn't returned in vector top-k
                
            b_score = doc_id_to_bm25[cid]["norm_bm25"] if cid in doc_id_to_bm25 else 0.0
            
            # Linear score fusion
            hybrid_score = 0.5 * v_score + 0.5 * b_score
            
            fused_chunks.append({
                "id": cid,
                "text": text,
                "metadata": metadata,
                "relevance_score": hybrid_score
            })

        # Sort combined candidates by fused score
        fused_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
        candidate_chunks = fused_chunks[:candidate_k]

        if not candidate_chunks:
            return []

        # 4. Apply LLM Reranking if Gemini API is available
        from config import is_gemini_api_active
        is_gemini_active = is_gemini_api_active()
        
        if is_gemini_active and len(candidate_chunks) > 1:
            try:
                reranked_chunks = self._llm_rerank(query, candidate_chunks, top_k)
                return reranked_chunks
            except Exception as e:
                print(f"LLM Reranking failed: {e}. Falling back to hybrid fused ranking.")
        
        # Fallback: Sort by fused hybrid score and take top_k
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
