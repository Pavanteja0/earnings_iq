from .base import BaseAgent

class SynthesisAgent(BaseAgent):
    """
    Lead Synthesis Agent that compiles quantitative and qualitative analysis 
    into a professional, publication-ready sell-side research brief.
    """
    def __init__(self):
        system_prompt = (
            "You are the Director of Research and Lead Sell-Side Equity Analyst. "
            "Your job is to synthesize raw financial statistics and qualitative call sentiments "
            "into a publication-ready Investment Research Brief.\n"
            "Constraints:\n"
            "1. Maintain a professional, objective, and sharp analytical tone.\n"
            "2. Structure the brief strictly as follows:\n"
            "   - **Header Block**: Company Name, Quarter, Analyst Rating, Current Price, Target Price, Date.\n"
            "   - **Executive Summary**: The single biggest takeaway from the quarter in 2 paragraphs.\n"
            "   - **Financial Dashboard Table**: Summarize key metrics.\n"
            "   - **Bull Thesis & Bear Thesis**: Detailed, structured bullet points containing specific financial facts and call details.\n"
            "   - **Confidence Score**: A score from 1 to 10 with a thorough explanation of alignment (management claims vs. actual disclosures).\n"
            "   - **Source Citations Index**: Table listing every cited source item.\n"
            "3. Ensure all citations are preserved in brackets (e.g., [10-Q, Page 8])."
        )
        from config import PREMIUM_GEMINI_MODEL
        super().__init__(
            name="Synthesis Writer",
            role="Compiles financial analyses into the final analyst-grade research brief.",
            system_prompt=system_prompt,
            model_name=PREMIUM_GEMINI_MODEL
        )

    def synthesize(self, quant_report: str, qual_report: str) -> str:
        """
        Synthesizes the final brief from quantitative and qualitative analyst inputs.
        """
        self.log("Synthesizing Brief", "Combining financial metrics and tone analyses.")
        
        user_prompt = (
            "Review the following draft analyses from your team:\n\n"
            f"=== Quantitative Analysis ===\n{quant_report}\n\n"
            f"=== Qualitative Sentiment Analysis ===\n{qual_report}\n\n"
            "Compile the final Research Brief. Make sure it reads like a top-tier sell-side report (e.g., Goldman Sachs, Morgan Stanley). "
            "Do not drop any key numbers, margins, segment metrics, or citations. Ensure the Bull/Bear theses are robust and analytical."
        )
        
        brief = self.run_llm(user_prompt, temperature=0.3)
        return brief

    def synthesize_direct(self, retriever, call_analysis_raw: str) -> str:
        """
        Directly queries the RAG retriever and synthesizes the research brief in a single LLM call.
        """
        self.log("Synthesizing Brief Direct (Fast Mode)", "Retrieving facts and writing brief concurrently.")
        
        # Retrieve key contexts from RAG database
        key_queries = [
            "revenue net income eps gross profit margin",
            "cloud services division segment revenues",
            "guidance outlook risks headwind challenges",
        ]
        
        grounding_context = []
        for q in key_queries:
            hits = retriever.retrieve(q, top_k=2)
            for hit in hits:
                meta = hit["metadata"]
                ref = f"[{meta.get('type')}, Page/Slide {meta.get('page')}]"
                grounding_context.append(f"Source Context: {hit['text']}\nReference: {ref}\n")
                
        context_str = "\n".join(grounding_context)
        
        user_prompt = (
            "You are the Director of Research. Directly compile a publication-ready Sell-Side Equity Research Brief "
            "using the original source contexts and qualitative call analysis below.\n\n"
            f"=== Source Contexts ===\n{context_str}\n\n"
            f"=== Call Analysis Raw ===\n{call_analysis_raw}\n\n"
            "Produce the final brief. Structure it with Header Block, Executive Summary, Financial Table, "
            "Bull/Bear Thesis, Confidence Score (1-10), and Source Citations Index. "
            "Be precise with numbers and include citations in brackets."
        )
        
        brief = self.run_llm(user_prompt, temperature=0.3)
        return brief

    def get_mock_response(self, user_prompt: str) -> str:
        return """# EarningsIQ Equity Research Brief
**Company**: Acme Corporation (NASDAQ: ACME)  
**Quarter**: Q3 Fiscal 2026  
**Analyst Rating**: Overweight (BUY)  
**Target Price**: $125.00 (Current: $108.50)  
**Date**: July 14, 2026  

---

### Executive Summary
Acme Corporation delivered a solid Q3 2026 performance, beating revenue expectations at $12.45B (+10% YoY) and showing resilient Gross Profit Margins of 44.2% (+70 bps YoY) [10-Q, Page 12]. The expansion was driven primarily by strong momentum in Cloud Services (+15.5% YoY) [10-Q, Page 16]. However, the quarter was marked by structural headwind pressures on operating expenses and severe CapEx investments, which grew faster than top-line revenues.

The analyst call revealed management defensiveness regarding Cloud Division margin compression sequentially, attributing it to accelerated server depreciation [Earnings Call, Q&A, 32:45]. While management maintains confidence in its enterprise SaaS shift, near-term hardware headwinds in Europe represent a key risk [Earnings Call, Q&A, 41:10]. We remain bullish on ACME's long-term enterprise market share, but advise near-term margin caution.

---

### Financial Performance Dashboard
| Metric | Q3 2026 | Q3 2025 | YoY Change | Source Citation |
| :--- | :--- | :--- | :--- | :--- |
| **Revenue** | $12.45B | $11.32B | +10.0% | [10-Q, Page 8] |
| **Gross Margin** | 44.2% | 43.5% | +70 bps | [10-Q, Page 12] |
| **Operating Margin** | 18.5% | 17.8% | +70 bps | [10-Q, Page 14] |
| **Net Income** | $1.82B | $1.64B | +11.0% | [10-Q, Page 8] |
| **Diluted EPS** | $0.88 | $0.78 | +12.8% | [10-Q, Page 8] |

---

### Investment Thesis

#### The Bull Case (Upside Catalyst)
1. **Cloud Services Scaling**: High-margin Cloud segment grew 15.5% YoY to $5.12B, expanding recurring revenue mix [10-Q, Page 16].
2. **Resilient Pricing Power**: Achieved a 70 bps YoY gross margin expansion despite supply chain headwinds, proving strong enterprise pricing power [10-Q, Page 12].
3. **Solid Cash Generation**: Generated $2.15B in operating cash flow, building cash reserves to $8.45B to fund CapEx expansion internally [10-Q, Page 4, 6].

#### The Bear Case (Downside Risks)
1. **Sequential Margin Erosion**: Gross margins shrank sequentially, and management was defensive about server depreciation offsets [Earnings Call, Q&A, 32:45].
2. **CapEx Overhang**: Substantial AI infrastructure buildout [Slide Deck, Slide 10] will weigh on near-term free cash flow yield.
3. **Macro Headwinds in Europe**: Enterprise spending delays are slowing hardware conversions, prompting cautious guidance for Q4 [Earnings Call, Q&A, 41:10].

---

### Confidence Score & Alignment Audit
**Score: 8 / 10 (High Confidence)**

**Alignment Rationale**: There is a strong consistency between management's remarks on SaaS transformation momentum and the segments reported in the 10-Q (+15.5% SaaS revenue). However, we penalize the score by 2 points because management downplayed the operating expense growth rate on the call, which actual disclosures showed was growing at 12.1% YoY (outpacing revenue growth). The citations verified that statements on pricing power and cash reserve strength are fully backed by 10-Q balance sheets."""
