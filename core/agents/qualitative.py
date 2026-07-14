from typing import List, Dict, Any
from .base import BaseAgent
from ..rag.retriever import Retriever

class QualitativeAgent(BaseAgent):
    """
    Qualitative / Sentiment Agent focused on earnings call audio, management tone, 
    analyst friction, and Q&A dynamics.
    """
    def __init__(self):
        system_prompt = (
            "You are a Senior Qualitative Research Analyst (Sell-Side). "
            "Your job is to read or listen to the earnings call materials and summarize the tone, sentiment, "
            "management confidence, and Q&A dynamic.\n"
            "Constraints:\n"
            "1. Focus on vocal cues, management hesitation, strategic pivots, and analyst pushback.\n"
            "2. Identify the top themes discussed in the Q&A session. Point out where analysts sounded skeptical "
            "and where management sounded defensive or overly cautious.\n"
            "3. Support every conclusion with direct quotes or specific context citations (e.g., [Earnings Call, Q&A Q3] or [Slide Deck, Slide 5]).\n"
            "4. Distinguish clearly between fact-based statements and executive narrative/spin."
        )
        super().__init__(
            name="Qualitative Analyst",
            role="Analyzes management tone, analyst Q&A friction, and strategic company messaging.",
            system_prompt=system_prompt
        )

    def analyze(self, retriever: Retriever, call_analysis_raw: str) -> str:
        """
        Combines retrieved transcript context with the raw audio/transcript analysis 
        to produce a detailed qualitative report.
        """
        self.log("Starting Analysis", "Retrieving analyst Q&A and management opening remarks.")
        
        # Retrieve context from the database regarding calls/decks
        queries = [
            ("Management opening remarks strategic growth pillars", "Transcript File"),
            ("Analyst pushback Q&A margins growth outlook concerns", "Transcript File")
        ]
        
        compiled_context = []
        for query, src_filter in queries:
            hits = retriever.retrieve(query, top_k=3, source_type=src_filter)
            for hit in hits:
                meta = hit["metadata"]
                ref = f"[{meta.get('type')}, Page/Slide {meta.get('page')}]"
                compiled_context.append(f"Source Reference: {ref}\nContent:\n{hit['text']}\n")
        
        # Add the raw audio analysis (which contains the tone/vocal cues from the audio parser)
        compiled_context.append(f"--- Audio Ingestion Raw Analysis ---\n{call_analysis_raw}")
        context_str = "\n".join(compiled_context)
        
        user_prompt = (
            "Based on the retrieved context and raw call analysis, write the qualitative section of the research brief.\n"
            "Provide:\n"
            "1. **Management Tone Audit**: Outline CEO/CFO confidence levels, strategic clarity, and vocal tone cues. "
            "Cite specific phrases or timestamps.\n"
            "2. **Analyst Friction & Q&A Dynamics**: Detail what issues analysts pressed hardest on (e.g., margin pressure, competitors, growth rates). "
            "Describe management's defense and highlight any pauses or hesitation.\n"
            "3. **Key Strategic Focus**: What are the top 2-3 mid-to-long term drivers mentioned in the call/presentation?"
        )
        
        report = self.run_llm(user_prompt, context=context_str)
        return report

    def get_mock_response(self, user_prompt: str) -> str:
        return (
            "### Qualitative & Sentiment Analysis Report (Mock Mode)\n\n"
            "#### 1. Management Tone Audit\n"
            "- **Executive Sentiment**: Overall tone was cautious but defensive. CEO emphasized 'operational efficiency' and 'cloud growth maturity,' "
            "but CFO's voice dropped when discussing hardware sales contraction, displaying slight hesitation. [Earnings Call, Q&A, 24:12]\n"
            "- **Management Quote**: *'We are navigating a tough macro environment, but our core SaaS metrics have never been healthier.'* [Earnings Call, Remarks]\n\n"
            "#### 2. Analyst Friction & Q&A Dynamics\n"
            "- **Operating Margins Under Pressure**: Analyst Toni Sacconaghi (Sanford Bernstein) pressed hard on the 200 bps sequential drop in Cloud division gross margins. "
            "CFO paused for approximately 3 seconds before responding with a defensive explanation about 'accelerated server depreciation' and 'upfront AI infrastructure costs.' [Earnings Call, Q&A, 32:45]\n"
            "- **Guidance Skepticism**: Analyst Katy Huberty (Morgan Stanley) questioned whether the Q4 revenue guidance of $12.8B-$13.1B (+5% YoY) was conservative given the Q3 double-digit growth. "
            "CEO responded that they see 'enterprise spending elongation' in Europe. [Earnings Call, Q&A, 41:10]\n\n"
            "#### 3. Key Strategic Focus\n"
            "- **AI Infrastructure Buildout**: Heavy upfront CapEx investment planned for 2026/2027 to scale the Cloud division [Slide Deck, Slide 10].\n"
            "- **Enterprise SaaS Shift**: Transitioning legacy on-premise hardware clients to cloud contracts, sacrificing short-term hardware margins for recurring revenues [Slide Deck, Slide 12]."
        )
