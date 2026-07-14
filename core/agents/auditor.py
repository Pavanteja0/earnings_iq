import re
from typing import Dict, Any, List
from .base import BaseAgent
from ..rag.retriever import Retriever

class AuditorAgent(BaseAgent):
    """
    Auditor Agent that verifies all citations, checks numerical accuracy, 
    calculates margins, and flags hallucinations or discrepancies.
    """
    def __init__(self):
        system_prompt = (
            "You are a Senior Financial Auditor and Compliance Officer for an Equity Research Firm.\n"
            "Your job is to audit research drafts for correctness, verification, and grounding.\n"
            "Constraints:\n"
            "1. Check every numerical claim. Verify if the math (e.g. YoY growth rate, margins) is correct.\n"
            "2. Cross-reference citations. Ensure that facts attributed to [10-Q, Page X] are actually in that source context.\n"
            "3. Flag any statement that is not fully supported by the provided source documents as a 'Discrepancy'.\n"
            "4. Provide a structured audit report: state whether the draft passed or failed, list any specific corrections, "
            "and output a finalized, corrected brief with correct figures."
        )
        super().__init__(
            name="Auditor Analyst",
            role="Audits citations, recalculates ratios, flags hallucinations, and produces the final certified brief.",
            system_prompt=system_prompt
        )

    def audit(self, brief: str, retriever: Retriever) -> Dict[str, Any]:
        """
        Performs a systematic audit of the research brief.
        Retrieves original context for citations and uses Gemini to verify grounding and math.
        """
        self.log("Auditing Brief", "Extracting citations and querying grounding sources.")
        
        # Step 1: Scan brief for bracketed citations like [10-Q, Page 8] or [Slide Deck, Slide 5]
        citations = re.findall(r"\[([^\]]+)\]", brief)
        self.log("Citations Found", f"Extracted {len(citations)} citations: {citations}")
        
        # Step 2: Fetch grounding context from RAG for the top cited terms
        # Let's retrieve context for terms in the brief that have numbers
        grounding_context = []
        numbered_sentences = [s for s in brief.split(".") if any(c.isdigit() for c in s)]
        
        for idx, sentence in enumerate(numbered_sentences[:8]):  # Check a representative sample of sentences
            query = sentence.strip()
            # Clean up the query a bit
            query = re.sub(r"\[[^\]]+\]", "", query)  # Remove brackets
            query = query[:120]  # Limit length
            
            hits = retriever.retrieve(query, top_k=2)
            for hit in hits:
                meta = hit["metadata"]
                ref = f"[{meta.get('type')}, Page/Slide {meta.get('page')}]"
                grounding_context.append(f"Grounding Fact: {hit['text']}\nReference: {ref}\n")
                
        context_str = "\n".join(grounding_context)
        
        # Step 3: Run the Auditor LLM to inspect the brief against retrieved facts
        user_prompt = (
            f"Review and audit this draft research brief:\n\n"
            f"=== Draft Brief ===\n{brief}\n\n"
            "Check every number, citation, and math statement in the brief against the grounding facts below. "
            "Identify any discrepancies or errors. If none are found, state 'Audit Status: PASSED'. "
            "Otherwise, state 'Audit Status: ADJUSTMENTS NEEDED' and list the corrections, followed by the complete corrected Brief."
        )
        
        audit_output = self.run_llm(user_prompt, context=context_str)
        
        # Run deterministic math verification
        from ..utils.math_verifier import verify_math_claims
        math_verification = verify_math_claims(brief)
        
        # Combine the LLM grounding audit and python math verification reports
        combined_report = (
            f"=== COMPLIANCE GROUNDING AUDIT ===\n{audit_output}\n\n"
            f"=== ARITHMETIC RECALCULATION AUDIT ===\n{math_verification['report']}"
        )
        
        # Parse audit output to determine status and generate the final audited brief
        status = "PASSED"
        # If either LLM flags discrepancies or Python math has accuracy < 100%
        if "ADJUSTMENTS NEEDED" in audit_output or "Discrepancy" in audit_output or math_verification["math_accuracy_score"] < 0.99:
            status = "ADJUSTMENTS NEEDED"
            
        # Extract corrected brief or default to the original brief if LLM didn't restructure it
        corrected_brief = brief
        if "### Corrected Brief" in audit_output:
            parts = audit_output.split("### Corrected Brief")
            corrected_brief = parts[-1].strip()
        elif "### Final Brief" in audit_output:
            parts = audit_output.split("### Final Brief")
            corrected_brief = parts[-1].strip()
            
        # Dynamically compute faithfulness score based on deterministic math correctness
        base_score = int(math_verification["math_accuracy_score"] * 100)
        if status == "ADJUSTMENTS NEEDED":
            # Penalize the score further for general semantic mismatches/hallucinations
            base_score = max(0, base_score - 15)
            
        return {
            "status": status,
            "audit_report": combined_report,
            "brief": corrected_brief,
            "faithfulness_score": base_score
        }

    def get_mock_response(self, user_prompt: str) -> str:
        # Check if we are testing a discrepancy (used in unit tests)
        if "18.9" in user_prompt or "discrepancy" in user_prompt.lower():
            return (
                "### Audit Status: ADJUSTMENTS NEEDED\n\n"
                "#### Discrepancies Found:\n"
                "- Stated Revenue of $18.90B in draft does not match the grounded RAG source, which states $12.45B ($12,448 million) on [10-Q, Page 8].\n"
                "- Stated growth rate of 10.0% is mathematically incorrect based on Q3 2026 revenue of $18.90B and Q3 2025 revenue of $11.32B.\n"
            )

        # Standard mockup output showing a successful audit pass
        return (
            "### Audit Status: PASSED\n\n"
            "#### Verification Log:\n"
            "- Verified Q3 Revenue of $12.45B in draft matches [10-Q, Page 8] value ($12,448 million).\n"
            "- Verified Gross Profit Margin of 44.2% matches [10-Q, Page 12] table ($5,502 million / $12,448 million = 44.2%).\n"
            "- Verified Operating Cash Flow of $2.15B matches [10-Q, Page 6] Cash Flows Statement.\n"
            "- Verified segment revenues for Cloud Division ($5.12B) and Enterprise Hardware ($4.85B) match segment disclosures [10-Q, Page 16].\n"
            "- Verified European macroeconomic headwinds citation aligns with Q&A session at [Earnings Call, Q&A, 41:10].\n"
            "- Calculated growth rates verified: Diluted EPS growth ($0.88 vs $0.78) is exactly 12.8% YoY.\n\n"
            "**Conclusion**: No hallucinations or mathematical discrepancies detected. The research brief is certified as factually grounded."
        )
