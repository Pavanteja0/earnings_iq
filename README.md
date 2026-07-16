# 📈 EarningsIQ

[![CI Pipeline](https://img.shields.io/github/actions/workflow/status/Pavanteja0/earnings_iq/ci.yml?branch=main&style=for-the-badge&logo=github)](https://github.com/Pavanteja0/earnings_iq/actions)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Pavanteja0/earnings_iq?style=for-the-badge&color=green)](https://github.com/Pavanteja0/earnings_iq/blob/main/LICENSE)
[![Streamlit App](https://img.shields.io/badge/Streamlit-Cloud-FF4B4B?style=for-the-badge&logo=streamlit)](https://earningsiq.streamlit.app)

An enterprise-grade, **Multimodal Financial Intelligence Multi-Agent System** that ingests SEC 10-Q reports, investor presentation decks, and earnings call audios/transcripts to synthesize factually grounded investment theses and run audit checks.

```
┌────────────────────────────────────────────────────────┐
│  Upload 10-Q, Slides, & Audio ────────► Ingest & Index │
└────────────────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────┐
│  Multi-Agent Debate ◄─────────────────► Retrieve RAG   │
└────────────────────────────────────────────────────────┘
    │ (Quant & Qual)
    ▼
┌────────────────────────────────────────────────────────┐
│  Deterministic Python Math Verify ────► Compile Brief  │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Features

* **Multimodal Ingestion**: Parses SEC 10-Q filings (`PyMuPDF`), slides presentations, and earnings call transcripts concurrently.
* **Hybrid RAG Retrieval**: Combines sparse keyword search (**BM25 Okapi**) and dense semantic search (**Gemini text-embedding-004**) with a linear fusion scorer.
* **Parallel Multi-Agent Orchestration**: Spawns concurrent analyst agents (📈 Quantitative, 🎙️ Qualitative) alongside Synthesis and Compliance Auditor agents.
* **Deterministic Math Recalculation**: Runs regular expression parser extractions and recalculates YoY changes and margins using a sandboxed Python execution loop to prevent hallucinations.
* **LLMOps Groundedness Dashboard**: Computes faithfulness, answer relevance, and calculation correctness metrics using a Gemini-as-a-judge suite.
* **Lightning Fast Execution**: Includes a **Fast Mode** that bypasses sequential steps to compile briefs and run auditing tasks concurrently in **~5 seconds**.

---

## 📁 Repository Structure

```
.
├── .github/                  # GitHub Actions and Issue/PR templates
│   ├── ISSUE_TEMPLATE/       # Templates for bug reports and feature requests
│   └── PULL_REQUEST_TEMPLATE.md
├── assets/                   # Visual graphs, diagrams, and UI mockups
├── core/                     # Source modules for EarningsIQ
│   ├── agents/               # Multi-agent implementations (Quant, Qual, Auditor)
│   ├── evals/                # LLMOps grounding evaluators
│   ├── ingestion/            # PDF and slide extraction algorithms
│   ├── rag/                  # Indexers, retrievers, and SQLite connectors
│   └── utils/                # Arithmetic verification helpers
├── docs/                     # Guides, design decision reports, and architecture
│   ├── architecture.md       # Technical system specifications
│   └── beginner_guide.md     # Rookie-friendly AI/RAG guide
├── tests/                    # Integration and unit tests
├── .env.example              # Environment variables template
├── CHANGELOG.md              # Historical releases logs
├── CONTRIBUTING.md           # Developer contributing setup guide
├── SECURITY.md               # Vulnerability reporting procedures
└── requirements.txt          # Third-party dependency manifest
```

---

## ⚙️ Quick Start

### 1. Installation
Clone the repository and set up a virtual environment:
```bash
git clone https://github.com/Pavanteja0/earnings_iq.git
cd earnings_iq
python -m venv venv

# Activate venv:
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Credentials
Copy `.env.example` to `.env` and paste your Gemini API key:
```bash
cp .env.example .env
# Edit .env and enter GEMINI_API_KEY
```

### 3. Run the App
Launch the Streamlit web dashboard locally:
```bash
streamlit run app.py
```

### 4. Run Tests
Verify configuration and pipeline stability:
```bash
python -m pytest tests/
```

---

## 🧠 System Architecture & Pipelines

### Hybrid Retrieval & Indexing
Each uploaded document is parsed page-by-page. EarningsIQ implements a persistent SQLite-backed **ChromaDB** client with batch writing. When a query is received, the retriever fetches candidates from two pipelines:
1. **Vector similarity**: Sharded semantic query similarity.
2. **BM25 Okapi**: Sparse term matching on alphanumeric regex token indexes.

```
                    ┌──► Vector Store (Gemini Embeddings) ──┐
Query ──────────────┤                                       ├──► Fused List ──► Top-K
                    └──► BM25 Index (Okapi TF-IDF) ─────────┘
```

### Prompt Engineering & Agent Debate
We utilize structured XML templates to coordinate the agent debate loop. The **Quantitative Agent** reviews numerical disclosures, the **Qualitative Agent** evaluates managerial confidence and risks, and the **Synthesis Agent** compiles the brief. Finally, the **Auditor Agent** cross-references citations and checks Python-based math verification reports to ensure absolute correctness.

---

## 📊 Example Queries & Verification Logs

```
Stated Claim: "Revenues expanded by 10.0% YoY to $12.45B."
Recalculated: (12,448 - 11,316) / 11,316 = 10.003% (Pass, within 1.5% tolerance)
Audit Status: PASSED (Verified [10-Q, Page 8])
```

| Stated Metric | Grounding File | Stated | Computed | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Gross Profit Margin** | `10-Q, Page 12` | 44.2% | 44.20% | ✅ VERIFIED |
| **Diluted EPS** | `10-Q, Page 8` | $0.88 | $0.88 | ✅ VERIFIED |
| **Revenue Growth** | `10-Q, Page 8` | 10.0% | 10.00% | ✅ VERIFIED |

---

## 🔮 Future Roadmap

* **GPU Vector Acceleration**: Shift vector collections to remote managed databases.
* **Auto-Generating Slide Vision Charts**: Ingest and describe complex diagrams and tables on slide presentation graphics using Gemini Vision.
* **Cross-Quarter Analysis**: Support comparison metrics across multiple historical quarters.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
