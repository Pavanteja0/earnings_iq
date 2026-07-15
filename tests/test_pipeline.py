import pytest
from pathlib import Path
from core.ingestion.pdf_doc import parse_10q_pdf
from core.ingestion.presentation import parse_presentation_deck
from core.ingestion.audio import analyze_call_audio
from core.rag.indexer import Indexer
from core.rag.retriever import Retriever
from core.orchestrator import Orchestrator

# Setup paths relative to the project root
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

@pytest.fixture(scope="session", autouse=True)
def ensure_sample_data():
    """Ensure that sample data files exist before running tests."""
    pdf_10q = DATA_DIR / "sample_acme_10q.pdf"
    pdf_deck = DATA_DIR / "sample_acme_deck.pdf"
    txt_transcript = DATA_DIR / "sample_acme_transcript.txt"
    
    if not (pdf_10q.exists() and pdf_deck.exists() and txt_transcript.exists()):
        # Run the sample generator
        import create_sample_data
        create_sample_data.main()

def test_pdf_parsing():
    """Tests that the 10-Q PDF parser correctly extracts sections and page details."""
    pdf_path = DATA_DIR / "sample_acme_10q.pdf"
    chunks = parse_10q_pdf(pdf_path)
    
    assert len(chunks) > 0
    # Check that metadata is correctly configured
    first_chunk = chunks[0]
    assert "text" in first_chunk
    assert "metadata" in first_chunk
    assert first_chunk["metadata"]["type"] == "10-Q"
    assert first_chunk["metadata"]["page"] == 1
    
    # Check section detection
    has_financial_statements = any("FINANCIAL STATEMENTS" in c["metadata"]["section"] for c in chunks)
    assert has_financial_statements

def test_deck_parsing():
    """Tests that the investor deck parser extracts raw text of slides."""
    deck_path = DATA_DIR / "sample_acme_deck.pdf"
    chunks = parse_presentation_deck(deck_path, use_vision=False) # run without vision for testing
    
    assert len(chunks) > 0
    assert chunks[0]["metadata"]["type"] == "Slide Deck"
    assert "SLIDE 1" in chunks[0]["text"]

def test_audio_transcript_parsing():
    """Tests that call audio parser handles text transcript fallbacks correctly."""
    transcript_path = DATA_DIR / "sample_acme_transcript.txt"
    call_data = analyze_call_audio(transcript_path)
    
    assert "transcript" in call_data
    assert "Sarah Jenkins" in call_data["transcript"]
    assert "analysis" in call_data
    assert call_data["metadata"]["type"] == "Transcript File"

def test_rag_index_and_retrieve():
    """Tests RAG indexing and retrieval flow with ChromaDB."""
    indexer = Indexer()
    indexer.reset_collection()
    
    # Add dummy chunks
    chunks = [
        {"text": "Acme gross margin expanded by 70 bps to 44.2% YoY.", "metadata": {"type": "10-Q", "page": 2, "source": "test_10q.pdf"}},
        {"text": "Cloud Division revenue reached $5.12B.", "metadata": {"type": "Slide Deck", "page": 2, "source": "test_deck.pdf"}},
    ]
    
    indexer.add_chunks(chunks)
    assert indexer.get_stats()["total_chunks"] == 2
    
    # Retrieve
    retriever = Retriever(indexer)
    hits = retriever.retrieve("gross margin expansion", top_k=1)
    
    assert len(hits) == 1
    assert "gross margin" in hits[0]["text"].lower()

def test_orchestrator_workflow():
    """Tests the orchestrator pipeline end-to-end."""
    orchestrator = Orchestrator()
    
    pdf_path = DATA_DIR / "sample_acme_10q.pdf"
    deck_path = DATA_DIR / "sample_acme_deck.pdf"
    transcript_path = DATA_DIR / "sample_acme_transcript.txt"
    
    # 1. Ingest
    stats = orchestrator.ingest_materials(pdf_path, deck_path, transcript_path, use_vision=False)
    assert stats["chunks_count"] > 0
    
    # 2. Run workflow
    results = orchestrator.execute_workflow(stats["call_analysis_raw"])
    assert "brief" in results
    assert "evals" in results
    assert "agent_logs" in results
    assert len(results["agent_logs"]) == 4  # 4 agents

def test_real_pdf_parsing():
    """Tests parsing on a real, messy SEC 10-K/10-Q PDF (using TSLA deck as source)."""
    pdf_path = DATA_DIR / "real_tsla_deck.pdf"
    assert pdf_path.exists(), "Real PDF was not downloaded."
    
    chunks = parse_10q_pdf(pdf_path, max_pages=15)
    assert len(chunks) > 0
    # Confirm it parses multiple pages and retains standard metadata (M13)
    assert any(c["metadata"]["page"] > 0 for c in chunks)
    assert all(c["metadata"]["type"] == "10-Q" for c in chunks)

def test_real_deck_parsing():
    """Tests parsing on a real, chart-heavy investor deck PDF (Tesla Investor Deck)."""
    deck_path = DATA_DIR / "real_tsla_deck.pdf"
    assert deck_path.exists(), "Real Tesla deck PDF was not downloaded."
    
    chunks = parse_presentation_deck(deck_path, use_vision=False, max_pages=15)
    assert len(chunks) > 0
    # Confirm it extracted textual sections from Tesla's slides
    assert any("TSLA" in c["text"] or "Tesla" in c["text"] for c in chunks)

def test_auditor_flags_discrepancy():
    """
    Correctness Test: Deliberately introduces a wrong number and arithmetic mistake
    in the draft brief, and verifies that the Auditor Agent successfully flags it.
    """
    indexer = Indexer()
    indexer.reset_collection()
    
    # 1. Index correct base numbers in RAG database
    correct_chunks = [
        {
            "text": "Acme reported Q3 2026 revenue of $12,448 million ($12.45B) and Q3 2025 revenue of $11,316 million ($11.32B).",
            "metadata": {"type": "10-Q", "page": 8, "source": "sample_acme_10q.pdf"}
        }
    ]
    indexer.add_chunks(correct_chunks)
    retriever = Retriever(indexer)
    
    # 2. Write a brief containing a falsified revenue number and incorrect growth math
    # Stated: Revenue is $18.90B (wrong, is $12.45B), and growth is 10.0% (wrong: (18.9 - 11.32)/11.32 = 66.9%)
    incorrect_brief = (
        "Acme Corporation delivered Q3 2026 performance. "
        "Revenue was $18.90B [10-Q, Page 8] compared to $11.32B in the prior year, representing a YoY growth of 10.0% [10-Q, Page 8]."
    )
    
    # 3. Execute the Audit
    from core.agents.auditor import AuditorAgent
    auditor = AuditorAgent()
    audit_res = auditor.audit(incorrect_brief, retriever)
    
    # 4. Assertions: Auditor must catch the discrepancies
    assert audit_res["status"] == "ADJUSTMENTS NEEDED"
    # Grounding score must be penalized due to math error
    assert audit_res["faithfulness_score"] < 100
    
    # Verify the audit log mentions the discrepancy or calculations
    report = audit_res["audit_report"].lower()
    assert "discrepancy" in report or "adjustments" in report or "error" in report

def test_orchestrator_workflow_fast_mode():
    """Tests the orchestrator pipeline in Fast Mode."""
    orchestrator = Orchestrator()
    pdf_path = DATA_DIR / "sample_acme_10q.pdf"
    deck_path = DATA_DIR / "sample_acme_deck.pdf"
    transcript_path = DATA_DIR / "sample_acme_transcript.txt"
    
    # Ingest
    stats = orchestrator.ingest_materials(pdf_path, deck_path, transcript_path, use_vision=False, max_pages=5)
    assert stats["chunks_count"] > 0
    
    # Run workflow in fast mode
    results = orchestrator.execute_workflow(stats["call_analysis_raw"], fast_mode=True)
    assert "brief" in results
    assert "evals" in results
    assert "agent_logs" in results
    # In fast mode, we skip Quant and Qual stages, so we expect exactly 2 active agents (Synthesis and Auditor)
    assert len(results["agent_logs"]) == 2


