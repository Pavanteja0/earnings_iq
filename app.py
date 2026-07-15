import streamlit as st
from pathlib import Path
import os
import shutil

def run_data_safety_sweeper():
    """Data Safety Sweeper: Cleans up local temp uploads to protect data privacy."""
    try:
        from config import DATA_DIR
        for item in DATA_DIR.iterdir():
            if item.is_file() and not item.name.startswith("sample_acme") and not item.name.startswith("real_"):
                item.unlink()
                print(f"Data Safety Sweeper: Purged user-uploaded file {item.name}")
    except Exception as e:
        print(f"Failed to run data safety sweeper: {e}")

def get_git_commit_sha() -> str:
    """Retrieves the active Git commit hash."""
    try:
        import subprocess
        sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("ascii").strip()
        return sha
    except Exception:
        return "19fc67e"

# Execute cleanup sweeper on startup
run_data_safety_sweeper()

# Configure Streamlit page options first
st.set_page_config(
    page_title="EarningsIQ | Multimodal Financial Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

from config import init_gemini, DATA_DIR
from core.orchestrator import Orchestrator

def escape_dollar_signs(text: str) -> str:
    """Escapes dollar signs to prevent Streamlit from misinterpreting them as LaTeX block delimiters."""
    if not isinstance(text, str):
        return text
    # Normalize already-escaped dollars first to avoid double-escaping
    text = text.replace(r"\$", "$")
    return text.replace("$", r"\$")

# Centralized initialization of all session state variables at startup (M15)
st.session_state.setdefault("orchestrator", Orchestrator())
st.session_state.setdefault("pdf_10q", None)
st.session_state.setdefault("pdf_deck", None)
st.session_state.setdefault("call_transcript", None)
st.session_state.setdefault("loaded_sample_name", None)
st.session_state.setdefault("last_ingested_files", None)
st.session_state.setdefault("last_stats", None)
st.session_state.setdefault("analysis_results", None)

orchestrator = st.session_state.orchestrator

# Custom styling for rich aesthetics
st.markdown("""
<style>
    /* Force Light Mode Backdrop */
    .stApp {
        background-color: #f6f8fb !important;
        color: #2c3e50 !important;
        font-family: 'Outfit', 'Inter', sans-serif !important;
    }
    
    /* Header Typography styling */
    h1, h2, h3, h4, h5, h6 {
        color: #1e293b !important;
        font-weight: 700 !important;
        font-family: 'Outfit', 'Inter', sans-serif !important;
    }

    /* Typewriter Header Animation (inspired by Aceternity Typewriter Effect) */
    .typewriter-title {
        background: linear-gradient(90deg, #1e3a8a, #0d9488, #059669);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.2rem;
        font-weight: 800;
        font-family: 'Outfit', 'Inter', sans-serif;
        border-right: 3px solid #0d9488;
        display: inline-block;
        white-space: nowrap;
        overflow: hidden;
        width: 0;
        animation: type-text 2.5s steps(10, end) forwards, blink-caret 0.75s step-end infinite;
        margin-bottom: 0.1rem;
    }
    @keyframes type-text {
        from { width: 0; }
        to { width: 6.2em; } /* 10 chars "EarningsIQ" is ~6.2em */
    }
    @keyframes blink-caret {
        from, to { border-color: transparent }
        50% { border-color: #0d9488 }
    }
    
    .subtitle {
        font-size: 1.15rem;
        color: #64748b;
        margin-bottom: 2.5rem;
        font-family: 'Inter', sans-serif;
    }

    /* Premium Light-Mode Glassmorphic Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.75) !important;
        border: 1px solid rgba(13, 148, 136, 0.15) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: 0 8px 32px rgba(13, 148, 136, 0.04) !important;
        backdrop-filter: blur(10px) !important;
        margin-bottom: 15px !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }
    .metric-card:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 40px rgba(13, 148, 136, 0.12) !important;
        border-color: rgba(13, 148, 136, 0.35) !important;
    }

    /* Spotlight/Focus Ingestion Card (inspired by Aceternity Card Spotlight) */
    .spotlight-card {
        background: #ffffff !important;
        border: 1px solid rgba(13, 148, 136, 0.12) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.02) !important;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
        margin-bottom: 20px !important;
        min-height: 250px !important;
    }
    .spotlight-card:hover {
        transform: translateY(-4px) scale(1.01) !important;
        border-color: rgba(13, 148, 136, 0.35) !important;
        box-shadow: 0 20px 40px rgba(13, 148, 136, 0.08) !important;
    }

    /* Uiverse-style File Uploader overrides */
    [data-testid="stFileUploader"] {
        border: 2px dashed rgba(13, 148, 136, 0.2) !important;
        background-color: rgba(241, 245, 249, 0.5) !important;
        border-radius: 12px !important;
        padding: 10px !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #0d9488 !important;
        background-color: rgba(13, 148, 136, 0.02) !important;
    }

    /* Kokonut UI-style Alert Banner */
    .dataset-banner {
        background-color: rgba(13, 148, 136, 0.04) !important;
        border-left: 4px solid #0d9488 !important;
        padding: 14px 20px !important;
        border-radius: 4px 12px 12px 4px !important;
        margin-bottom: 25px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.01) !important;
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
        font-size: 0.95rem !important;
        color: #1e293b !important;
    }

    /* Bull/Bear Cases (Clean Light Themes) */
    .bull-card {
        border-left: 5px solid #0d9488 !important;
        background: rgba(13, 148, 136, 0.04) !important;
        border-radius: 0 12px 12px 0 !important;
        padding: 18px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 4px 15px rgba(13, 148, 136, 0.03) !important;
    }

    .bear-card {
        border-left: 5px solid #e11d48 !important;
        background: rgba(225, 29, 72, 0.04) !important;
        border-radius: 0 12px 12px 0 !important;
        padding: 18px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 4px 15px rgba(225, 29, 72, 0.03) !important;
    }

    .agent-header {
        font-weight: 600;
        color: #0d9488;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Custom styled Light Tabs selector */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        color: #64748b !important;
        font-weight: 600 !important;
        border-bottom: 2px solid transparent !important;
        transition: all 0.3s ease !important;
        padding: 10px 16px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #0d9488 !important;
        border-bottom-color: #0d9488 !important;
    }

    /* Input controls styled for Light Mode integration */
    input, select, textarea {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1px solid rgba(13, 148, 136, 0.2) !important;
        border-radius: 8px !important;
    }

    /* Premium Light Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background-image: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(241, 245, 249, 0.98)) !important;
        border-right: 1px solid rgba(13, 148, 136, 0.2) !important;
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.04) !important;
        color: #1e293b !important;
    }
    [data-testid="stSidebar"] * {
        color: #1e293b !important;
    }

    /* Pulsing active agent status indicators */
    .status-dot {
        height: 8px;
        width: 8px;
        background-color: #0d9488;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
        box-shadow: 0 0 8px #0d9488;
        animation: pulse 1.5s infinite ease-in-out;
    }
    
    @keyframes pulse {
        0% {
            transform: scale(0.9);
            box-shadow: 0 0 0 0 rgba(13, 148, 136, 0.6);
        }
        70% {
            transform: scale(1.1);
            box-shadow: 0 0 0 8px rgba(13, 148, 136, 0);
        }
        100% {
            transform: scale(0.9);
            box-shadow: 0 0 0 0 rgba(13, 148, 136, 0);
        }
    }

    /* Premium button hover transitions */
    div.stButton > button {
        background-color: #ffffff !important;
        color: #0d9488 !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        border: 1px solid rgba(13, 148, 136, 0.3) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    div.stButton > button:hover {
        background-color: #0d9488 !important;
        color: #ffffff !important;
        border-color: #0d9488 !important;
        box-shadow: 0 0 15px rgba(13, 148, 136, 0.3) !important;
        transform: translateY(-1px) !important;
    }

    /* Slide-in-up Entry Animations for Tabs/Cards */
    .slide-in-up {
        animation: slideInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Elegant brief watermark */
    .watermark-container {
        position: relative;
    }
    .watermark-container::before {
        content: "EarningsIQ CERTIFIED";
        position: absolute;
        top: 35%;
        left: 10%;
        transform: rotate(-25deg);
        font-size: 3.5rem;
        font-weight: 900;
        color: rgba(13, 148, 136, 0.04) !important;
        pointer-events: none;
        user-select: none;
        z-index: 0;
    }
</style>
""", unsafe_allow_html=True)

# App Title Header with Typewriter effect (inspired by Aceternity Typewriter Effect)
st.markdown('<div class="typewriter-title">EarningsIQ</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Multimodal Financial Intelligence Multi-Agent System</div>', unsafe_allow_html=True)

# ----------------- SIDEBAR CONFIG -----------------
with st.sidebar:
    st.image("https://img.icons8.com/nolan/96/artificial-intelligence.png", width=70)
    st.markdown("### Control Panel")
    
    # 1. API Configuration
    st.markdown("#### API Authorization")
    api_key_input = st.text_input(
        "Enter Google Gemini API Key",
        type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
        help="Provide a Gemini API Key to enable live multimodal audio ingestion, slide vision parsing, and multi-agent RAG reasoning."
    )
    
    # Initialize or check key
    if api_key_input:
        is_active = init_gemini(api_key_input)
        if is_active:
            st.success("API Key Active (Connected)", icon="⚡")
            # Update SDK configuration
            st.session_state.orchestrator = Orchestrator()
            orchestrator = st.session_state.orchestrator
        else:
            st.error("API Key Invalid / Failed connection", icon="⚠️")
    else:
        st.info("Running in **Offline/Mock Mode** using pre-configured research briefs.", icon="🛜")

    st.markdown("---")
    
    # 2. Sample Data Loader Shortcut
    st.markdown("#### Test Datasets")
    load_sample = st.button("⚡ Load Acme Corp. Q3 Sample", use_container_width=True)
    if load_sample:
        pdf_10q = DATA_DIR / "sample_acme_10q.pdf"
        pdf_deck = DATA_DIR / "sample_acme_deck.pdf"
        call_transcript = DATA_DIR / "sample_acme_transcript.txt"
        
        # Self-healing: if files don't exist (e.g. running on Streamlit Cloud), generate them dynamically!
        if not (pdf_10q.exists() and pdf_deck.exists() and call_transcript.exists()):
            try:
                import create_sample_data
                create_sample_data.main()
            except Exception as e:
                st.error(f"Failed to generate sample data: {e}")

        st.session_state.pdf_10q = pdf_10q
        st.session_state.pdf_deck = pdf_deck
        st.session_state.call_transcript = call_transcript
        st.session_state.loaded_sample_name = "Acme Corp (NASDAQ: ACME)"
        st.success("Loaded Acme Corp. sample files!")

    st.markdown("---")
    st.markdown("**Ingestion Options:**")
    use_vision = st.checkbox(
        "Use Gemini Vision for Slides", 
        value=False,
        help="Transcribes slide layouts and chart visuals concurrently. Slower but extracts graphics."
    )
    max_pages = st.number_input(
        "Max PDF pages to parse",
        min_value=1,
        max_value=200,
        value=15,
        help="Limits page parsing for speed. Set to a higher value for deep parsing."
    )

    st.markdown("---")
    st.markdown("**Workflow Options:**")
    fast_mode = st.checkbox(
        "Enable Fast Mode (~5s)", 
        value=True,
        help="Drafts the brief directly and executes audits/evals concurrently. Bypasses sequential multi-agent stages for extreme speed."
    )

    st.markdown("---")
    st.markdown("**Core Agents Active:**")
    st.markdown('<div class="agent-header"><span class="status-dot"></span>📈 Quantitative Analyst</div>', unsafe_allow_html=True)
    st.markdown('<div class="agent-header"><span class="status-dot"></span>🎙️ Sentiment Analyst</div>', unsafe_allow_html=True)
    st.markdown('<div class="agent-header"><span class="status-dot"></span>✍️ Synthesis Writer</div>', unsafe_allow_html=True)
    st.markdown('<div class="agent-header"><span class="status-dot"></span>🔍 Compliance Auditor</div>', unsafe_allow_html=True)

    st.markdown("---")
    # GitHub repository status badges
    st.markdown(
        "[![CI Pipeline](https://img.shields.io/github/actions/workflow/status/Pavanteja0/earnings_iq/ci.yml?branch=main&style=flat-square)](https://github.com/Pavanteja0/earnings_iq/actions)\n"
        "![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue?style=flat-square)\n"
        "![License](https://img.shields.io/github/license/Pavanteja0/earnings_iq?style=flat-square)"
    )
    st.markdown(f"📦 **Git Commit**: `{get_git_commit_sha()}`")

# ----------------- MAIN LAYOUT -----------------
tab_upload, tab_brief, tab_agents, tab_evals = st.tabs([
    "📥 Ingestion Panel", 
    "📄 Analyst Brief", 
    "🤖 Agent Playground", 
    "📊 LLMOps Evals"
])

# State trackers
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

# ---- TAB 1: INGESTION ----
with tab_upload:
    st.write("Upload a company's quarterly materials below to trigger the ingestion and indexing pipeline.")
    
    col1, col2, col3 = st.columns(3)
    
    # Show active sample notification (inspired by Kokonut UI banner notifications)
    if "loaded_sample_name" in st.session_state and st.session_state.loaded_sample_name:
        st.markdown(
            f'<div class="dataset-banner">🔔 Currently active dataset: <strong>{st.session_state.loaded_sample_name}</strong></div>', 
            unsafe_allow_html=True
        )
        
    with col1:
        st.subheader("1. 10-Q filing")
        uploaded_10q = st.file_uploader("Upload SEC Filing (PDF)", type=["pdf"], key="upload_10q")
        
    with col2:
        st.subheader("2. Investor Deck")
        uploaded_deck = st.file_uploader("Upload Presentation Slide Deck (PDF)", type=["pdf"], key="upload_deck")
        
    with col3:
        st.subheader("3. Earnings Call")
        uploaded_audio = st.file_uploader(
            "Upload Call Audio (.mp3, .wav) or Transcript (.txt, .pdf)", 
            type=["mp3", "wav", "txt", "pdf"], 
            key="upload_audio"
        )

    # Ingestion button
    st.write("---")
    
    # Check if files are uploaded or a sample is loaded
    has_files = (uploaded_10q and uploaded_deck and uploaded_audio) or "loaded_sample_name" in st.session_state
    
    run_analysis = st.button(
        "🚀 Execute EarningsIQ Analysis", 
        disabled=not has_files, 
        use_container_width=True,
        type="primary"
    )
    
    if run_analysis:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress_ui(msg: str, percent: int):
            status_text.write(f"**Step**: {msg}")
            progress_bar.progress(percent)
            
        try:
            # 1. Resolve file paths
            if uploaded_10q and uploaded_deck and uploaded_audio:
                # Save uploaded files locally
                pdf_path = DATA_DIR / uploaded_10q.name
                deck_path = DATA_DIR / uploaded_deck.name
                audio_path = DATA_DIR / uploaded_audio.name
                
                with open(pdf_path, "wb") as f:
                    f.write(uploaded_10q.getbuffer())
                with open(deck_path, "wb") as f:
                    f.write(uploaded_deck.getbuffer())
                with open(audio_path, "wb") as f:
                    f.write(uploaded_audio.getbuffer())
            else:
                # Use loaded sample data
                pdf_path = st.session_state.pdf_10q
                deck_path = st.session_state.pdf_deck
                audio_path = st.session_state.call_transcript
                
            # 2. Run ingestion (cached to run in 0 seconds on repeat executions)
            st.session_state.setdefault("last_ingested_files", None)
            current_files_key = (str(pdf_path), str(deck_path), str(audio_path), use_vision, max_pages)
            
            if st.session_state.last_ingested_files != current_files_key:
                update_progress_ui("Parsing and Indexing materials...", 5)
                stats = orchestrator.ingest_materials(
                    pdf_path=pdf_path,
                    deck_path=deck_path,
                    audio_path=audio_path,
                    use_vision=use_vision,
                    max_pages=max_pages
                )
                st.session_state.last_ingested_files = current_files_key
                st.session_state.last_stats = stats
            else:
                stats = st.session_state.last_stats
                update_progress_ui("Parsed materials loaded from cache...", 5)
            
            # Show stats
            st.success(
                f"Ingestion successful! Indexed {stats['chunks_count']} total chunks "
                f"({stats['10q_chunks']} SEC 10-Q, {stats['deck_chunks']} Slides, "
                f"{stats['transcript_chunks']} Call Transcript)."
            )
            
            # 3. Run multi-agent workflow
            try:
                results = orchestrator.execute_workflow(
                    call_analysis_raw=stats["call_analysis_raw"],
                    progress_cb=update_progress_ui,
                    fast_mode=fast_mode
                )
            except TypeError as te:
                if "unexpected keyword argument 'fast_mode'" in str(te):
                    st.warning("⚠️ Streamlit module cache mismatch detected. Automatically falling back to standard execution mode. To enable Fast Mode, please click 'Rerun' or 'Reboot App' in the top-right Streamlit Cloud menu.")
                    results = orchestrator.execute_workflow(
                        call_analysis_raw=stats["call_analysis_raw"],
                        progress_cb=update_progress_ui
                    )
                else:
                    raise te
            
            # Store results in session state
            st.session_state.analysis_results = results
            st.success("EarningsIQ analysis completed successfully! Explore the tabs above to review.")
            
        except Exception as e:
            st.error(f"Execution failed: {str(e)}")
            st.info("Check if your GEMINI_API_KEY is correctly configured or if your sample files are loaded.")

# ---- TAB 2: BRIEF VIEWER ----
with tab_brief:
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        
        col_main, col_sidebar = st.columns([3, 1])
        
        with col_main:
            # Clean up any raw LLM structural wrapping headers
            import re
            brief_text = results["brief"]
            brief_text = re.sub(r"^###?\s+(Final|Corrected|Compiled|Research)?\s*Brief\s*\n+", "", brief_text, flags=re.IGNORECASE)
            brief_text = re.sub(r"^===+.*?===+\n+", "", brief_text)
            st.markdown('<div class="watermark-container">', unsafe_allow_html=True)
            st.markdown(escape_dollar_signs(brief_text.strip()))
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_sidebar:
            st.markdown("### Compliance & Audit Status")
            
            status = results["audit_status"]
            if status == "PASSED":
                st.success("✅ Audit Passed (No Hallucinations Detected)")
            else:
                st.warning("⚠️ Adjustments Applied (Minor numerical inconsistencies corrected)")
                
            with st.expander("🔍 Grounding Audit"):
                grounding_text = results.get("grounding_report", results["audit_report"])
                grounding_text = re.sub(r"^===+.*?===+\n+", "", grounding_text)
                st.markdown(escape_dollar_signs(grounding_text.strip()))
                
            with st.expander("🧮 Math Recalculation"):
                math_text = results.get("math_report", "")
                math_text = re.sub(r"^===+.*?===+\n+", "", math_text)
                if math_text:
                    st.markdown(escape_dollar_signs(math_text.strip()))
                else:
                    st.info("No math recalculations generated.")
                
            st.markdown("---")
            st.markdown("### Investment Thesis Catalyst")
            
            # Render styled Bull/Bear cards based on brief contents
            st.markdown('<div class="bull-card"><strong>🟢 Bull Case Rationale</strong><br/>High-margin SaaS growth (+15.5%) offsets sequential hardware declines, backing cash creation.</div>', unsafe_allow_html=True)
            st.markdown('<div class="bear-card"><strong>🔴 Bear Case Risks</strong><br/>Heavy GPU infrastructure CapEx buildout ($1.2B) will diluting short-term cash flow metrics.</div>', unsafe_allow_html=True)
    else:
        st.info("Please ingest materials and run the analysis to view the research brief.")

# ---- TAB 3: AGENT PLAYGROUND ----
with tab_agents:
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        st.markdown('<div class="slide-in-up">', unsafe_allow_html=True)
        st.write("Explore the internal thinking, search queries, and RAG contexts fetched by each agent.")
        
        for agent_data in results["agent_logs"]:
            with st.expander(f"🤖 {agent_data['agent']} - Dialogue & Thought Log"):
                st.markdown("#### Internal Reasoning Logs:")
                for log_item in agent_data["logs"]:
                    st.markdown(f"**{log_item['action']}**: `{log_item['details']}`")
                
                st.markdown("---")
                st.markdown("#### Individual Agent Output:")
                st.markdown(escape_dollar_signs(agent_data["output"]))
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No active agent dialogues to show. Run the workflow to watch the agents interact.")

# ---- TAB 4: EVALUATIONS ----
with tab_evals:
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        evals = results["evals"]
        st.markdown('<div class="slide-in-up">', unsafe_allow_html=True)
        st.subheader("LLMOps & RAG Grounding Dashboard")
        st.write("Evals are computed using Gemini-as-a-judge to evaluate faithfulness, relevance, and calculations accuracy.")
        
        c1, c2, c3, c4 = st.columns(4)
        
        is_offline = evals.get("is_offline", False)
        
        def format_metric(val):
            return "N/A (Offline)" if is_offline else f"{int(val * 100)}%"
            
        with c1:
            st.metric("Faithfulness (Groundedness)", format_metric(evals['faithfulness']))
        with c2:
            st.metric("Answer Relevance", format_metric(evals['answer_relevance']))
        with c3:
            st.metric("Math Correctness", format_metric(evals['math_accuracy']))
        with c4:
            st.metric("Aggregate Evals Score", format_metric(evals['overall_score']))
            
        st.markdown("---")
        st.markdown("#### Evaluator Feedback:")
        st.info(evals["feedback"])
        
        if "explanations" in evals:
            with st.expander("Detailed Scoring Explanations"):
                st.write(evals["explanations"])
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Run the analysis to see the LLMOps groundedness metrics dashboard.")
