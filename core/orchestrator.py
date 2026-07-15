import time
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional

from .ingestion.pdf_doc import parse_10q_pdf
from .ingestion.presentation import parse_presentation_deck
from .ingestion.audio import analyze_call_audio

from .rag.indexer import Indexer
from .rag.retriever import Retriever

from .agents.quantitative import QuantitativeAgent
from .agents.qualitative import QualitativeAgent
from .agents.synthesis import SynthesisAgent
from .agents.auditor import AuditorAgent

from .evals.metrics import evaluate_brief

class Orchestrator:
    """
    Main orchestrator for the EarningsIQ Multi-Agent system.
    Manages the lifecycle of ingestion, indexing, agent discussions, auditing, and evaluation.
    """
    def __init__(self):
        self.indexer = Indexer()
        self.retriever = Retriever(self.indexer)
        
        # Instantiate agent team
        self.quant_agent = QuantitativeAgent()
        self.qual_agent = QualitativeAgent()
        self.synth_agent = SynthesisAgent()
        self.auditor_agent = AuditorAgent()

    def ingest_materials(
        self, 
        pdf_path: Path, 
        deck_path: Path, 
        audio_path: Path,
        use_vision: bool = True,
        max_pages: int = -1
    ) -> Dict[str, Any]:
        """
        Runs the parsing and ingestion pipeline for all uploaded files
        and indexes the output chunks into ChromaDB.
        """
        print("Ingestion started...")
        self.indexer.reset_collection()
        
        all_chunks = []
        
        # 1. Parse 10-Q / 10-K
        print(f"Parsing 10-Q: {pdf_path}")
        chunks_10q = parse_10q_pdf(pdf_path, max_pages=max_pages)
        all_chunks.extend(chunks_10q)
        
        # 2. Parse slide deck
        print(f"Parsing Investor Presentation: {deck_path}")
        chunks_deck = parse_presentation_deck(deck_path, use_vision=use_vision, max_pages=max_pages)
        all_chunks.extend(chunks_deck)
        
        # 3. Analyze earnings call audio/transcript
        # (This is returned as a summary report for qualitative context)
        print(f"Parsing Call Audio: {audio_path}")
        call_raw = analyze_call_audio(audio_path)
        
        # Add transcript chunks to RAG database for specific citation matching
        transcript_text = call_raw.get("transcript", "")
        # Split transcript into paragraph chunks for the indexer
        transcript_paragraphs = [p.strip() for p in transcript_text.split("\n\n") if p.strip()]
        chunks_transcript = []
        for idx, para in enumerate(transcript_paragraphs):
            chunks_transcript.append({
                "text": para,
                "metadata": {
                    "page": idx // 3 + 1,  # Mock page/segment grouping
                    "source": audio_path.name,
                    "type": "Transcript File"
                }
            })
        all_chunks.extend(chunks_transcript)
        
        # 4. Index all chunks into ChromaDB
        self.indexer.add_chunks(all_chunks)
        
        return {
            "chunks_count": len(all_chunks),
            "10q_chunks": len(chunks_10q),
            "deck_chunks": len(chunks_deck),
            "transcript_chunks": len(chunks_transcript),
            "call_analysis_raw": call_raw.get("analysis", "")
        }

    def execute_workflow(
        self, 
        call_analysis_raw: str,
        progress_cb: Optional[Callable[[str, int], None]] = None,
        fast_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Runs the Multi-Agent team execution flow:
        - Standard Mode: Quantitative -> Qualitative -> Synthesis -> Auditor -> Evals (sequential)
        - Fast Mode: Synthesis Direct -> (Auditor & Evals concurrently in parallel)
        """
        agent_logs = []
        
        def update_progress(msg: str, percent: int):
            if progress_cb:
                progress_cb(msg, percent)
            time.sleep(0.5)

        # Clear agent logs from previous run
        self.quant_agent.logs.clear()
        self.qual_agent.logs.clear()
        self.synth_agent.logs.clear()
        self.auditor_agent.logs.clear()

        import concurrent.futures

        if fast_mode:
            # 1. Direct Synthesis (retrieves and drafts in a single step)
            update_progress("Synthesizing Research Brief directly (Fast Mode)...", 30)
            draft_brief = self.synth_agent.synthesize_direct(self.retriever, call_analysis_raw)
            agent_logs.append({"agent": self.synth_agent.name, "logs": list(self.synth_agent.logs), "output": draft_brief})

            # 2. Concurrently run Auditor and LLMOps Evals in parallel
            update_progress("Auditing citations & evaluating quality in parallel...", 70)
            
            # Fetch unique contexts from Synthesis retrieval to ground Evals
            unique_contexts = []
            for log in self.synth_agent.logs:
                if log["action"] == "Retrieving Context" and "Query:" in log["details"]:
                    query = log["details"].split("Query: '")[1].split("'")[0]
                    hits = self.retriever.retrieve(query, top_k=2)
                    for h in hits:
                        if h["text"] not in unique_contexts:
                            unique_contexts.append(h["text"])
                            
            if not unique_contexts:
                # Fallback context in case logging differed
                hits = self.retriever.retrieve("revenue net income eps gross profit margin", top_k=5)
                unique_contexts = [h["text"] for h in hits]

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                future_audit = executor.submit(self.auditor_agent.audit, draft_brief, self.retriever)
                future_evals = executor.submit(evaluate_brief, draft_brief, unique_contexts)
                
                audit_res = future_audit.result()
                eval_metrics = future_evals.result()

            agent_logs.append({"agent": self.auditor_agent.name, "logs": list(self.auditor_agent.logs), "output": audit_res["audit_report"]})
            final_brief = audit_res["brief"]
            update_progress("Workflow completed successfully!", 100)

            return {
                "brief": final_brief,
                "audit_report": audit_res["audit_report"],
                "grounding_report": audit_res["grounding_report"],
                "math_report": audit_res["math_report"],
                "audit_status": audit_res["status"],
                "evals": eval_metrics,
                "agent_logs": agent_logs
            }

        # --- STANDARD MODE (Full Sequential Multi-Agent Flow) ---
        # Step 1 & 2: Concurrently run Quantitative & Qualitative analyses in parallel
        update_progress("Initiating Quantitative & Qualitative Analysts in parallel...", 20)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_quant = executor.submit(self.quant_agent.analyze, self.retriever)
            future_qual = executor.submit(self.qual_agent.analyze, self.retriever, call_analysis_raw)
            
            quant_report = future_quant.result()
            qual_report = future_qual.result()
            
        agent_logs.append({"agent": self.quant_agent.name, "logs": list(self.quant_agent.logs), "output": quant_report})
        agent_logs.append({"agent": self.qual_agent.name, "logs": list(self.qual_agent.logs), "output": qual_report})

        # Step 3: Synthesis Research Brief Drafting
        update_progress("Initiating Synthesis Agent to draft the Research Brief...", 50)
        draft_brief = self.synth_agent.synthesize(quant_report, qual_report)
        agent_logs.append({"agent": self.synth_agent.name, "logs": list(self.synth_agent.logs), "output": draft_brief})

        # Step 4: Auditor & Citation Check
        update_progress("Initiating Auditor Agent to verify citations and calculations...", 70)
        audit_res = self.auditor_agent.audit(draft_brief, self.retriever)
        agent_logs.append({"agent": self.auditor_agent.name, "logs": list(self.auditor_agent.logs), "output": audit_res["audit_report"]})
        
        final_brief = audit_res["brief"]

        # Step 5: Evaluate RAG & Grounding Quality (LLMOps Evals)
        update_progress("Running RAG Faithfulness & Math Accuracy Evaluations...", 90)
        unique_contexts = []
        for log in self.quant_agent.logs + self.qual_agent.logs:
            if log["action"] == "Retrieving Context" and "Query:" in log["details"]:
                query = log["details"].split("Query: '")[1].split("'")[0]
                hits = self.retriever.retrieve(query, top_k=2)
                for h in hits:
                    if h["text"] not in unique_contexts:
                        unique_contexts.append(h["text"])
                        
        eval_metrics = evaluate_brief(final_brief, unique_contexts)
        update_progress("Workflow completed successfully!", 100)

        return {
            "brief": final_brief,
            "audit_report": audit_res["audit_report"],
            "grounding_report": audit_res["grounding_report"],
            "math_report": audit_res["math_report"],
            "audit_status": audit_res["status"],
            "evals": eval_metrics,
            "agent_logs": agent_logs
        }
