# EarningsIQ: Multimodal Financial Intelligence Multi-Agent System

EarningsIQ is an analyst-grade AI system that ingests a public company's quarterly earnings materials—the call audio, 10-Q/10-K report, and investor presentation deck—and generates a professional sell-side equity research brief complete with citations, a detailed bull/bear thesis, a confidence score, and LLMOps evaluations.

## 🚀 Key Features

* **Multimodal Ingestion Pipeline**:
  * **SEC Filing Parser**: Section-aware chunking and extraction of dense text/tables from 10-Q/10-K PDFs.
  * **Investor Slide Deck Parser**: Renders slide pages as PNGs and applies Gemini Vision to analyze visual charts, graphs, and performance metrics.
  * **Call Audio Analyzer**: Uploads and transcribes earnings call audio (.mp3/.wav) natively using the Gemini File API to analyze management tone and Q&A verbal cues.
* **RAG Done Right**:
  * Persistent vector storage using ChromaDB.
  * Custom embedding function integrated with Gemini's `text-embedding-004` model.
  * Hybrid search (vector similarity + keyword BM25) coupled with LLM-based reranking.
* **Multi-Agent Orchestration**:
  * **Quantitative Analyst**: Extracts statistics and financial statements, computes margins/growth, and checks arithmetic consistency.
  * **Qualitative Analyst**: Evaluates management confidence, tone shifts, and analyst Q&A friction.
  * **Synthesis Writer**: Combines insights into a structured sell-side brief layout.
  * **Compliance Auditor**: Reviews drafts, checks claims against RAG source contexts, and certifies/corrects numbers.
* **LLMOps Grounding Evaluations**:
  * Features a built-in evaluator (Gemini-as-a-judge) grading the output on Faithfulness, Answer Relevance, and Math Accuracy.
* **Interactive Dashboard**:
  * Modern Streamlit-based UI displaying live progress bars, citations indexes, and an **Agent Playground** to audit the internal thinking logs of each agent.

---

## 🛠️ Local Setup Instructions

1. Clone this repository and navigate to the project directory:
   ```bash
   git clone <your-repository-url>
   cd earnings_iq
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate

   pip install -r requirements.txt
   ```

3. Set up environment variables by copying `.env.template` to `.env`:
   ```bash
   cp .env.template .env
   ```
   Add your Google Gemini API key to `.env`. *(If no key is provided, the app runs in Offline/Mock Mode automatically).*

4. Launch the Streamlit application:
   ```bash
   streamlit run app.py
   ```

---

## ☁️ Deployment (Streamlit Community Cloud)

This app is fully compatible with Streamlit Community Cloud:
1. Push your code to a public GitHub repository.
2. Visit [share.streamlit.io](https://share.streamlit.io) and connect your GitHub account.
3. Select your repository, the `main` branch, and set the entrypoint file path to `app.py`.
4. Click **Deploy**!
