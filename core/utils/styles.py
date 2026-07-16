def get_custom_css() -> str:
    """Returns the custom CSS styles override block for Light-Mode glassmorphic layouts."""
    return """
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
"""
