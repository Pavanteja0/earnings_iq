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
        use_vision: bool = True
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
        chunks_10q = parse_10q_pdf(pdf_path)
        all_chunks.extend(chunks_10q)
        
        # 2. Parse slide deck
        print(f"Parsing Investor Presentation: {deck_path}")
        chunks_deck = parse_presentation_deck(deck_path, use_vision=use_vision)
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
        progress_cb: Optional[Callable[[str, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Runs the Multi-Agent team execution flow:
        Quantitative -> Qualitative -> Synthesis -> Auditor -> Evals
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

        # Step 1: Quantitative Financial Analysis
        update_progress("Initiating Quantitative Analyst Agent...", 10)
        quant_report = self.quant_agent.analyze(self.retriever)
        agent_logs.append({"agent": self.quant_agent.name, "logs": list(self.quant_agent.logs), "output": quant_report})

        # Step 2: Qualitative Call & Sentiment Analysis
        update_progress("Initiating Qualitative Sentiment Agent...", 30)
        qual_report = self.qual_agent.analyze(self.retriever, call_analysis_raw)
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
        # Pull out unique content pieces retrieved during the run
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
            "audit_status": audit_res["status"],
            "evals": eval_metrics,
            "agent_logs": agent_logs
        }
