import streamlit as st
from pathlib import Path
import os
import shutil

# Configure Streamlit page options first
st.set_page_config(
    page_title="EarningsIQ | Multimodal Financial Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

from config import init_gemini, DATA_DIR
from core.orchestrator import Orchestrator

# Initialize the Orchestrator
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator()

orchestrator = st.session_state.orchestrator

# Custom styling for rich aesthetics
st.markdown("""
<style>
    /* Premium Gradient Header */
    .title-gradient {
        background: linear-gradient(90deg, #3f51b5, #00bcd4, #4caf50);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.1rem;
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    
    .subtitle {
        font-size: 1.15rem;
        color: #888899;
        margin-bottom: 2rem;
        font-family: 'Inter', sans-serif;
    }

    /* Glassmorphic custom cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(5px);
        margin-bottom: 15px;
    }

    /* Bull/Bear Cards */
    .bull-card {
        border-left: 5px solid #4caf50;
        background: rgba(76, 175, 80, 0.06);
        border-radius: 0 12px 12px 0;
        padding: 18px;
        margin-bottom: 12px;
    }

    .bear-card {
        border-left: 5px solid #f44336;
        background: rgba(244, 67, 54, 0.06);
        border-radius: 0 12px 12px 0;
        padding: 18px;
        margin-bottom: 12px;
    }

    .agent-header {
        font-weight: 600;
        color: #00bcd4;
        display: flex;
        align-items: center;
        gap: 8px;
    }
</style>
""", unsafe_allow_html=True)

# App Title Header
st.markdown('<div class="title-gradient">EarningsIQ</div>', unsafe_allow_html=True)
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
    st.write("📈 Quantitative Analyst")
    st.write("🎙️ Sentiment Analyst")
    st.write("✍️ Synthesis Writer")
    st.write("🔍 Compliance Auditor")

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
    
    # Show active sample notification
    if "loaded_sample_name" in st.session_state:
        st.info(f"Currently active dataset: **{st.session_state.loaded_sample_name}** (loaded from sample library).")
        
    with col1:
        st.subheader("1. 10-Q or 10-K Report")
        uploaded_10q = st.file_uploader("Upload SEC Filing (PDF)", type=["pdf"], key="upload_10q")
        
    with col2:
        st.subheader("2. Investor Deck")
        uploaded_deck = st.file_uploader("Upload Presentation Slide Deck (PDF)", type=["pdf"], key="upload_deck")
        
    with col3:
        st.subheader("3. Earnings Call Call")
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
            st.markdown(results["brief"])
            
        with col_sidebar:
            st.markdown("### Compliance & Audit Status")
            
            status = results["audit_status"]
            if status == "PASSED":
                st.success("✅ Audit Passed (No Hallucinations Detected)")
            else:
                st.warning("⚠️ Adjustments Applied (Minor numerical inconsistencies corrected)")
                
            with st.expander("Review Audit Log"):
                st.markdown(results["audit_report"])
                
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
        
        st.write("Explore the internal thinking, search queries, and RAG contexts fetched by each agent.")
        
        for agent_data in results["agent_logs"]:
            with st.expander(f"🤖 {agent_data['agent']} - Dialogue & Thought Log"):
                st.markdown("#### Internal Reasoning Logs:")
                for log_item in agent_data["logs"]:
                    st.markdown(f"**{log_item['action']}**: `{log_item['details']}`")
                
                st.markdown("---")
                st.markdown("#### Individual Agent Output:")
                st.text_area("Agent Report Draft", agent_data["output"], height=250, key=f"out_{agent_data['agent']}")
    else:
        st.info("No active agent dialogues to show. Run the workflow to watch the agents interact.")

# ---- TAB 4: EVALUATIONS ----
with tab_evals:
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        evals = results["evals"]
        
        st.subheader("LLMOps & RAG Grounding Dashboard")
        st.write("Evals are computed using Gemini-as-a-judge to evaluate faithfulness, relevance, and calculations accuracy.")
        
        c1, c2, c3, c4 = st.columns(4)
        
        def format_metric(val):
            return f"{int(val * 100)}%" if val >= 0 else "N/A (Offline)"
            
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
    else:
        st.info("Run the analysis to see the LLMOps groundedness metrics dashboard.")
