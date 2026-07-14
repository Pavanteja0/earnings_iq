from typing import List, Dict, Any
from .base import BaseAgent
from ..rag.retriever import Retriever

class QuantitativeAgent(BaseAgent):
    """
    Financial Analyst Agent focused on quantitative metrics, financial statements, 
    calculations (margins, growth), and checking targets/guidance.
    """
    def __init__(self):
        system_prompt = (
            "You are a Senior Quantitative Equity Research Analyst (Sell-Side). "
            "Your job is to extract, verify, and tabulate key financial figures from the provided earnings materials.\n"
            "Constraints:\n"
            "1. Focus strictly on numbers, percentages, and dollar amounts.\n"
            "2. Be extremely precise. Double-check all calculations (e.g., Year-over-Year growth, Gross Margin %, EPS beats).\n"
            "3. State values exactly as they are in the text. Distinguish between 'thousands', 'millions', and 'billions'.\n"
            "4. Provide the exact source citation for every single number (e.g., [10-Q, Page 14] or [Slide Deck, Slide 8]).\n"
            "5. If a metric is not available, clearly state 'Not Disclosed' or 'N/A' rather than guessing.\n\n"
            "Format your output with clear markdown headings, tables, and bullet points."
        )
        super().__init__(
            name="Quantitative Analyst",
            role="Extracts and tabulates financial tables, computes key ratios, and validates arithmetic metrics.",
            system_prompt=system_prompt
        )

    def analyze(self, retriever: Retriever) -> str:
        """
        Runs multiple target queries to retrieve relevant financial blocks and
        synthesizes the financial metrics report.
        """
        self.log("Starting Analysis", "Retrieving financial statements, segment results, and outlook guidance.")
        
        # Define target search queries for financial details
        queries = [
            ("Revenue, Net Income, and Diluted EPS performance relative to expectations", "10-Q"),
            ("Margins: Gross profit margin, operating margins, YoY margin expansion or compression", "10-Q"),
            ("Balance Sheet: Cash, cash equivalents, total debt, and cash flow from operations", "10-Q"),
            ("Segment Performance: Product categories or geographic divisions revenue", "10-Q"),
            ("Guidance and Outlook: Next quarter or fiscal year projections", "Slide Deck")
        ]
        
        compiled_context = []
        for query, src_filter in queries:
            self.log("Retrieving Context", f"Query: '{query}' in source: {src_filter}")
            hits = retriever.retrieve(query, top_k=3, source_type=src_filter)
            for hit in hits:
                meta = hit["metadata"]
                ref = f"[{meta.get('type')}, Page/Slide {meta.get('page')}]"
                compiled_context.append(f"Source Reference: {ref}\nContent:\n{hit['text']}\n")
                
        context_str = "\n".join(compiled_context)
        
        user_prompt = (
            "Based on the retrieved context, generate the quantitative section of the equity research brief.\n"
            "Provide:\n"
            "1. A core 'Quarterly Earnings Summary Table' comparing Revenue, Gross Margin, Operating Margin, Net Income, and Diluted EPS "
            "for the current quarter vs the prior-year quarter (YoY change in % or basis points). Include citations in the table.\n"
            "2. A segment breakdown of revenue and growth rates.\n"
            "3. Balance sheet health check (cash balance, total debt, operating cash flow).\n"
            "4. Current guidance vs actual outcomes.\n\n"
            "Remember: every number must have a bracketed source citation referencing the document and page/slide."
        )
        
        report = self.run_llm(user_prompt, context=context_str)
        return report

    def get_mock_response(self, user_prompt: str) -> str:
        return (
            "### Quantitative Analysis Report (Mock Mode)\n\n"
            "| Metric | Q3 2026 | Q3 2025 | YoY Change | Source Citation |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            "| **Revenue** | $12.45B | $11.32B | +10.0% | [10-Q, Page 8] |\n"
            "| **Gross Profit Margin** | 44.2% | 43.5% | +70 bps | [10-Q, Page 12] |\n"
            "| **Operating Margin** | 18.5% | 17.8% | +70 bps | [10-Q, Page 14] |\n"
            "| **Net Income** | $1.82B | $1.64B | +11.0% | [10-Q, Page 8] |\n"
            "| **Diluted EPS** | $0.88 | $0.78 | +12.8% | [10-Q, Page 8] |\n\n"
            "#### Segment Performance\n"
            "- **Cloud Division Services**: $5.12B (41.1% of total), +15.5% YoY [10-Q, Page 16]\n"
            "- **Enterprise Hardware**: $4.85B (39.0% of total), +4.2% YoY [10-Q, Page 16]\n"
            "- **Consumer Devices**: $2.48B (19.9% of total), +11.2% YoY [10-Q, Page 17]\n\n"
            "#### Balance Sheet & Cash Flows\n"
            "- **Cash & Cash Equivalents**: $8.45B [10-Q, Page 4]\n"
            "- **Total Debt**: $3.20B [10-Q, Page 5]\n"
            "- **Operating Cash Flow**: $2.15B [10-Q, Page 6]\n\n"
            "#### Guidance Outlook\n"
            "- Next quarter revenue guided to $12.8B - $13.1B (+5% YoY) [Slide Deck, Slide 14]\n"
            "- Operating margin targeted at 19.0% - 19.5% [Slide Deck, Slide 15]"
        )
