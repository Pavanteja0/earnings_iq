# Beginner's Guide to EarningsIQ

Welcome to **EarningsIQ**! If you are new to AI, Large Language Models (LLMs), or financial analysis, this guide is designed for you. It explains the core concepts and shows how the project works behind the scenes without the jargon.

---

## 🔍 The Problem We Solve
Every quarter, public companies release mountains of financial information:
1. **10-Q Reports**: Huge PDF documents filled with tables, margins, and balance sheets.
2. **Investor Slides**: Visual presentation decks summarizing key performance indicators (KPIs).
3. **Earnings Call Transcripts**: Text transcripts of the CEO and CFO explaining the results and answering tough analyst questions.

Reading and cross-referencing all these documents is exhausting. **EarningsIQ** automates this by building an AI-driven team that analyzes these files for you in seconds.

---

## 🧠 Core Concepts Explained Simply

### 1. What is Retrieval-Augmented Generation (RAG)?
Standard AI models (like ChatGPT or Gemini) are trained on general internet data. They do not know about a company's private, newly released Q3 earnings report. If you ask them about it, they will either say they don't know, or worse, they will **hallucinate** (make up numbers).

**RAG** solves this by:
* **Retrieving** the exact paragraphs from the Q3 documents that match your question.
* **Augmenting** (adding) those paragraphs to your question.
* **Generating** the final answer using the model, forcing it to base its response *only* on the retrieved paragraphs.

```
[ Your Question ] ────────► [ Search In Files ] ────────► [ Found Paragraphs ]
                                                                │
[ Factually Correct Answer ] ◄──────── [ LLM Model ] ◄──────────┘
```

### 2. What are Embeddings?
Computers do not understand the meaning of words the way humans do. To help the computer search through text based on *ideas* rather than exact keyword matches, we use **Embeddings**.

An Embedding model converts a paragraph of text into a long list of numbers (a vector). Paragraphs with similar meanings end up having numbers that are mathematically close to each other.
* *"Revenues expanded significantly"* and *"Top-line sales grew"* will have very similar embeddings, even though they use completely different words!

### 3. What is a Vector Database?
A standard database searches for exact matches (like looking up an employee ID). A **Vector Database** stores our paragraph embeddings (vectors) and searches for paragraphs that are *semantically similar* (similar in meaning) to a query. We use **ChromaDB** to store and search our vectors locally.

### 4. What is Prompt Orchestration?
Instead of sending a giant, unstructured pile of text to the AI and asking for a summary, EarningsIQ uses a **Multi-Agent Orchestrator**. We split the work among specialized AI "agents":
* 📈 **Quantitative Agent**: Focuses strictly on the financial numbers and growth rates.
* 🎙️ **Sentiment Agent**: Focuses on management's tone, confidence, and risks.
* ✍️ **Synthesis Writer**: Combines both analyses into a publication-ready brief.
* 🔍 **Compliance Auditor**: Cross-references every single number in the brief against the original PDF page numbers to ensure 100% accuracy.

---

## 🔄 How Documents Move Through EarningsIQ

```
┌─────────────────┐      ┌──────────────┐      ┌─────────────┐      ┌─────────────┐
│ Ingest PDF/Text │ ───► │ Split Chunks │ ───► │ Embed Text  │ ───► │ Store in DB │
└─────────────────┘      └──────────────┘      └─────────────┘      └─────────────┘
```

1. **Ingestion**: You upload a 10-Q PDF, an Investor slide deck, and a transcript.
2. **Text Chunking**: The PDFs are split page-by-page into small, manageable paragraphs (chunks).
3. **Embedding**: Each chunk is passed through the Gemini embedding API to generate its numerical vector.
4. **Indexing**: The chunks and their vectors are saved into ChromaDB.
5. **Retrieval**: When you ask a question, the system searches ChromaDB and pulls the top matching chunks.
6. **Agent Synthesis & Audit**: The AI agents compile the brief, and the Auditor agent runs Python math calculations to double-check that the AI didn't make any arithmetic mistakes.
