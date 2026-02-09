import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from sources.reddit_source import RedditSource
from sources.reddit_rss_source import RedditRSSSource  # NEW: RSS fallback
from sources.hackernews_source import HackerNewsSource
from sources.stackoverflow_source import StackOverflowSource
from sources.github_source import GitHubSource
from sources.producthunt_source import ProductHuntSource
from sources.reddit_pushshift import RedditPushshiftSource
from sources.linkedin_source import LinkedInSource
from analyzer import Analyzer
from database import Database
from trend_analyzer import TrendAnalyzer
from aggregator import Aggregator

# Page Config
st.set_page_config(
    page_title="Problem Hunter",
    page_icon="🎯",
    layout="wide"
)

# Load Environment Variables
load_dotenv()

# Initialize database (singleton)
@st.cache_resource
def get_database():
    return Database()

def save_api_key_to_env(key_name: str, key_value: str):
    """Save API key to .env file for persistence."""
    import os
    from pathlib import Path
    
    env_path = Path('.env')
    
    # Read existing .env content
    existing_lines = []
    if env_path.exists():
        with open(env_path, 'r') as f:
            existing_lines = f.readlines()
    
    # Update or add the key
    key_found = False
    updated_lines = []
    for line in existing_lines:
        if line.startswith(f"{key_name}="):
            updated_lines.append(f"{key_name}={key_value}\n")
            key_found = True
        else:
            updated_lines.append(line)
    
    # Add new key if not found
    if not key_found:
        updated_lines.append(f"{key_name}={key_value}\n")
    
    # Write back to .env
    with open(env_path, 'w') as f:
        f.writelines(updated_lines)

def main():
    # 🎨 RETRO-FUTURISTIC BRUTALIST DATA HUNTER DESIGN
    st.markdown("""
    <style>
    /* Import bold, distinctive fonts */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600;700&display=swap');
    
    /* === CORE DESIGN SYSTEM === */
    :root {
        /* Retro-futuristic color palette */
        --neon-green: #00ff41;
        --neon-cyan: #00f0ff;
        --neon-pink: #ff006e;
        --terminal-bg: #0a0e27;
        --terminal-dark: #050816;
        --grid-color: rgba(0, 255, 65, 0.1);
        --text-primary: #e0e0e0;
        --text-secondary: #a0a0a0;
    }
    
    /* Global reset and base */
    * {
        font-family: 'Space Grotesk', -apple-system, sans-serif;
        letter-spacing: -0.02em;
    }
    
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    /* === STREAMLIT HEADER/TOOLBAR FIX === */
    header[data-testid="stHeader"] {
        background-color: var(--terminal-dark) !important;
        border-bottom: 2px solid var(--neon-green) !important;
    }
    
    /* Hide Streamlit branding */
    header[data-testid="stHeader"] > div:first-child {
        background-color: var(--terminal-dark) !important;
    }
    
    /* Style the toolbar buttons */
    header[data-testid="stHeader"] button {
        color: var(--neon-cyan) !important;
        background-color: transparent !important;
        border: 1px solid var(--neon-cyan) !important;
        border-radius: 0 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.75rem !important;
        padding: 0.25rem 0.5rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    
    header[data-testid="stHeader"] button:hover {
        background-color: var(--neon-cyan) !important;
        color: var(--terminal-dark) !important;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.5) !important;
    }
    
    /* Style the menu icon */
    header[data-testid="stHeader"] svg {
        color: var(--neon-cyan) !important;
    }
    
    /* === MENU POPUPS AND DROPDOWNS === */
    /* Main menu popup */
    [data-testid="stHeaderActionElements"] [data-baseweb="popover"] {
        background-color: var(--terminal-dark) !important;
        border: 2px solid var(--neon-cyan) !important;
        border-radius: 0 !important;
    }
    
    /* Menu items */
    [data-testid="stHeaderActionElements"] [role="menuitem"],
    [data-testid="stHeaderActionElements"] [role="option"] {
        background-color: var(--terminal-dark) !important;
        color: var(--neon-cyan) !important;
        font-family: 'JetBrains Mono', monospace !important;
        border-radius: 0 !important;
    }
    
    [data-testid="stHeaderActionElements"] [role="menuitem"]:hover,
    [data-testid="stHeaderActionElements"] [role="option"]:hover {
        background-color: var(--neon-cyan) !important;
        color: var(--terminal-dark) !important;
    }
    
    /* Dropdown menus (select boxes) */
    [data-baseweb="popover"] {
        background-color: var(--terminal-dark) !important;
        border: 2px solid var(--neon-cyan) !important;
        border-radius: 0 !important;
    }
    
    [data-baseweb="menu"] {
        background-color: var(--terminal-dark) !important;
        border-radius: 0 !important;
    }
    
    [data-baseweb="menu"] [role="option"] {
        background-color: var(--terminal-dark) !important;
        color: var(--neon-cyan) !important;
        font-family: 'JetBrains Mono', monospace !important;
        border-radius: 0 !important;
    }
    
    [data-baseweb="menu"] [role="option"]:hover {
        background-color: var(--neon-cyan) !important;
        color: var(--terminal-dark) !important;
    }
    
    /* Selected option */
    [data-baseweb="menu"] [aria-selected="true"] {
        background-color: rgba(0, 255, 65, 0.2) !important;
        color: var(--neon-green) !important;
    }
    
    /* Expander dropdown content */
    [data-testid="stExpander"] [data-baseweb="popover"] {
        background-color: var(--terminal-dark) !important;
        border: 2px solid var(--neon-cyan) !important;
    }
    
    /* === UNIVERSAL MENU/DROPDOWN OVERRIDES === */
    /* Target ALL emotion cache divs that might be menus/dropdowns */
    div[class*="st-emotion-cache"] div[class*="st-emotion-cache"] {
        background-color: var(--terminal-dark) !important;
    }
    
    /* Target all list items */
    ul[class*="st-emotion-cache"] li,
    ul li[class*="st-emotion-cache"] {
        background-color: var(--terminal-dark) !important;
        color: var(--neon-cyan) !important;
    }
    
    ul[class*="st-emotion-cache"] li:hover,
    ul li[class*="st-emotion-cache"]:hover {
        background-color: var(--neon-cyan) !important;
        color: var(--terminal-dark) !important;
    }
    
    /* Nuclear option - target ALL divs with role listbox/menu */
    div[role="listbox"],
    div[role="menu"] {
        background-color: var(--terminal-dark) !important;
        border: 2px solid var(--neon-cyan) !important;
        border-radius: 0 !important;
    }
    
    div[role="listbox"] > *,
    div[role="menu"] > * {
        background-color: var(--terminal-dark) !important;
        color: var(--neon-cyan) !important;
    }
    
    /* === TERMINAL GRID BACKGROUND === */
    .stApp {
        background-color: var(--terminal-bg);
        background-image: 
            linear-gradient(var(--grid-color) 1px, transparent 1px),
            linear-gradient(90deg, var(--grid-color) 1px, transparent 1px);
        background-size: 50px 50px;
        background-position: -1px -1px;
        position: relative;
    }
    
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 50% 50%, transparent 0%, var(--terminal-dark) 100%);
        pointer-events: none;
        z-index: 0;
    }
    
    /* Scanline effect overlay */
    .stApp::after {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: repeating-linear-gradient(
            0deg,
            rgba(0, 255, 65, 0.03) 0px,
            transparent 1px,
            transparent 2px,
            rgba(0, 255, 65, 0.03) 3px
        );
        pointer-events: none;
        z-index: 1;
        opacity: 0.5;
    }
    
    /* === BRUTALIST HEADER === */
    .main-header {
        background: var(--terminal-dark);
        border: 3px solid var(--neon-green);
        border-radius: 0;
        padding: 3rem 2rem;
        margin-bottom: 3rem;
        position: relative;
        overflow: hidden;
        box-shadow: 
            0 0 30px rgba(0, 255, 65, 0.3),
            inset 0 0 50px rgba(0, 255, 65, 0.05);
    }
    
    .main-header::before {
        content: '[ SCAN MODE: ACTIVE ]';
        position: absolute;
        top: 10px;
        right: 20px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: var(--neon-green);
        text-transform: uppercase;
        letter-spacing: 2px;
        opacity: 0.7;
        animation: blink 2s infinite;
        border: 1px solid var(--neon-green);
        padding: 0.25rem 0.5rem;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.3);
    }
    
    @keyframes blink {
        0%, 50%, 100% { opacity: 0.7; }
        25%, 75% { opacity: 0.3; }
    }
    
    .main-header::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, 
            transparent 0%, 
            var(--neon-cyan) 50%, 
            transparent 100%);
        animation: scan 3s linear infinite;
    }
    
    @keyframes scan {
        0% { transform: translateY(0); }
        100% { transform: translateY(200px); }
    }
    
    .main-header h1 {
        color: var(--neon-green);
        font-size: 4rem;
        font-weight: 700;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: -0.05em;
        text-shadow: 
            0 0 10px var(--neon-green),
            0 0 20px var(--neon-green),
            0 0 30px var(--neon-green);
        line-height: 0.9;
    }
    
    .main-header .subtitle {
        color: var(--neon-cyan);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
        margin-top: 1rem;
        text-transform: uppercase;
        letter-spacing: 3px;
        opacity: 0.9;
    }
    
    .main-header .glitch {
        position: relative;
        display: inline-block;
    }
    
    /* === SIDEBAR TERMINAL STYLE === */
    section[data-testid="stSidebar"] {
        background: var(--terminal-dark) !important;
        border-right: 3px solid var(--neon-green) !important;
        box-shadow: inset 0 0 50px rgba(0, 255, 65, 0.1);
    }
    
    section[data-testid="stSidebar"] > div {
        background: transparent !important;
    }
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: var(--neon-cyan) !important;
        font-family: 'JetBrains Mono', monospace !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-size: 0.9rem !important;
        border-bottom: 2px solid var(--neon-cyan);
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* === BRUTALIST BUTTONS === */
    .stButton > button {
        background: var(--terminal-dark);
        color: var(--neon-green);
        border: 3px solid var(--neon-green);
        border-radius: 0;
        padding: 1rem 2rem;
        font-weight: 700;
        font-size: 1rem;
        transition: all 0.2s ease;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-family: 'JetBrains Mono', monospace;
        box-shadow: 
            0 0 20px rgba(0, 255, 65, 0.3),
            inset 0 0 20px rgba(0, 255, 65, 0.05);
    }
    
    .stButton > button:hover {
        background: var(--neon-green);
        color: var(--terminal-dark);
        box-shadow: 
            0 0 30px rgba(0, 255, 65, 0.6),
            0 0 50px rgba(0, 255, 65, 0.4);
        transform: translateY(-2px);
    }
    
    /* === TERMINAL INPUT FIELDS === */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: var(--terminal-dark);
        border: 2px solid var(--neon-cyan);
        border-radius: 0;
        color: var(--neon-cyan);
        padding: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--neon-green);
        box-shadow: 
            0 0 20px rgba(0, 255, 65, 0.5),
            inset 0 0 10px rgba(0, 255, 65, 0.1);
        color: var(--neon-green);
    }
    
    /* === CHECKBOX TERMINAL STYLE === */
    .stCheckbox {
        color: var(--text-primary) !important;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
    }
    
    .stCheckbox label {
        color: var(--text-primary) !important;
    }
    
    /* === SELECT BOXES === */
    .stSelectbox > div > div {
        background: var(--terminal-dark);
        border: 2px solid var(--neon-cyan);
        border-radius: 0;
        color: var(--neon-cyan);
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Select box dropdown arrow */
    .stSelectbox svg {
        color: var(--neon-cyan) !important;
    }
    
    /* Select box when open */
    .stSelectbox [data-baseweb="select"] > div {
        background-color: var(--terminal-dark) !important;
        border-color: var(--neon-green) !important;
    }
    
    /* === RADIO BUTTONS === */
    .stRadio > div {
        background: var(--terminal-dark);
        border: 2px solid var(--neon-pink);
        padding: 1rem;
        border-radius: 0;
    }
    
    .stRadio label {
        color: var(--text-primary) !important;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* === DATA CARDS === */
    .result-card {
        background: var(--terminal-dark);
        border: 2px solid var(--neon-cyan);
        border-radius: 0;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
        position: relative;
        box-shadow: 
            0 0 20px rgba(0, 240, 255, 0.2),
            inset 0 0 30px rgba(0, 240, 255, 0.05);
        border-left: 4px solid var(--neon-cyan);
    }
    
    .result-card:hover {
        border-color: var(--neon-green);
        border-left-color: var(--neon-green);
        transform: translateX(5px);
        box-shadow: 
            0 0 30px rgba(0, 255, 65, 0.4),
            inset 0 0 30px rgba(0, 255, 65, 0.1);
    }
    
    .result-card::before {
        content: '>';
        position: absolute;
        left: -15px;
        top: 50%;
        transform: translateY(-50%);
        color: var(--neon-green);
        font-size: 2rem;
        font-weight: 700;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .result-card:hover::before {
        opacity: 1;
    }
    
    /* === TYPOGRAPHY === */
    h1, h2, h3 {
        color: var(--neon-green) !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: -0.02em;
    }
    
    p, label, span, div {
        color: var(--text-primary) !important;
    }
    
    /* === METRICS WITH TERMINAL STYLE === */
    [data-testid="stMetricValue"] {
        color: var(--neon-green) !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        font-family: 'JetBrains Mono', monospace !important;
        text-shadow: 0 0 20px rgba(0, 255, 65, 0.5);
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--neon-cyan) !important;
        font-family: 'JetBrains Mono', monospace !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        font-size: 0.75rem !important;
    }
    
    /* === ALERTS === */
    .stAlert {
        background: var(--terminal-dark);
        border: 2px solid var(--neon-pink);
        border-radius: 0;
        color: var(--text-primary);
        font-family: 'JetBrains Mono', monospace;
    }
    
    .stSuccess {
        border-color: var(--neon-green);
        background: rgba(0, 255, 65, 0.1);
    }
    
    .stError {
        border-color: var(--neon-pink);
        background: rgba(255, 0, 110, 0.1);
    }
    
    /* === EXPANDERS === */
    .streamlit-expanderHeader {
        background: var(--terminal-dark);
        border: 2px solid var(--neon-cyan);
        border-radius: 0;
        color: var(--neon-cyan) !important;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
    }
    
    /* === DATAFRAMES === */
    .stDataFrame {
        background: var(--terminal-dark);
        border: 2px solid var(--neon-green);
        border-radius: 0;
    }
    
    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: var(--terminal-dark);
        border: 2px solid var(--neon-cyan);
        border-radius: 0;
        padding: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-right: 2px solid var(--neon-cyan);
        border-radius: 0;
        color: var(--text-secondary);
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
        padding: 1rem 2rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--neon-green);
        color: var(--terminal-dark);
    }
    
    /* === DIVIDERS === */
    hr {
        border: none;
        border-top: 2px solid var(--neon-cyan);
        margin: 2rem 0;
        opacity: 0.5;
    }
    
    /* === TERMINAL SCROLLBAR === */
    ::-webkit-scrollbar {
        width: 12px;
        height: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--terminal-dark);
        border-left: 2px solid var(--neon-green);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--neon-green);
        border-radius: 0;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--neon-cyan);
    }
    
    /* === LOADING SPINNER === */
    .stSpinner > div {
        border-top-color: var(--neon-green) !important;
        border-right-color: var(--neon-cyan) !important;
    }
    
    /* === ASYMMETRIC LAYOUT ACCENTS === */
    .stApp > div:first-child {
        position: relative;
    }
    
    .stApp > div:first-child::before {
        content: '';
        position: fixed;
        top: 0;
        right: 0;
        width: 200px;
        height: 200px;
        border-left: 3px solid var(--neon-pink);
        border-bottom: 3px solid var(--neon-pink);
        opacity: 0.3;
        pointer-events: none;
        z-index: 1000;
    }
    
    .stApp > div:first-child::after {
        content: '';
        position: fixed;
        bottom: 0;
        left: 0;
        width: 150px;
        height: 150px;
        border-right: 3px solid var(--neon-cyan);
        border-top: 3px solid var(--neon-cyan);
        opacity: 0.3;
        pointer-events: none;
        z-index: 1000;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 🎯 BRUTALIST HEADER
    st.markdown("""
    <div class="main-header">
        <h1><span class="glitch">⚡ PROBLEM HUNTER</span></h1>
        <p class="subtitle">[ AI-POWERED SAAS OPPORTUNITY SCANNER ]</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar Configuration
    st.sidebar.header("⚙️ Configuration")
    
    st.sidebar.subheader("🔑 API Keys")
    
    # Load from environment first
    load_dotenv()
    default_openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    default_reddit_id = os.getenv("REDDIT_CLIENT_ID", "")
    default_reddit_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
    default_github_token = os.getenv("GITHUB_TOKEN", "")
    default_ph_token = os.getenv("PRODUCTHUNT_TOKEN", "")
    
    # OpenRouter API Key (Required)
    openrouter_api_key = st.sidebar.text_input(
        "OpenRouter API Key (Required)",
        value=default_openrouter_key,
        type="password",
        help="Get from https://openrouter.ai/settings/keys"
    )
    
    # Save button for OpenRouter API key
    if openrouter_api_key and openrouter_api_key != default_openrouter_key:
        if st.sidebar.button("💾 Save OpenRouter API Key"):
            save_api_key_to_env("OPENROUTER_API_KEY", openrouter_api_key)
            st.sidebar.success("✅ Saved to .env file!")
            st.rerun()
    
    # Optional API Keys (Expandable)
    with st.sidebar.expander("🔓 Optional API Keys", expanded=False):
        st.markdown("*These are optional - some sources work without them!*")
        
        # Reddit
        st.markdown("**Reddit Official API**")
        reddit_client_id = st.text_input(
            "Reddit Client ID",
            value=default_reddit_id,
            type="password"
        )
        reddit_client_secret = st.text_input(
            "Reddit Client Secret",
            value=default_reddit_secret,
            type="password"
        )
        
        if (reddit_client_id and reddit_client_id != default_reddit_id) or \
           (reddit_client_secret and reddit_client_secret != default_reddit_secret):
            if st.button("💾 Save Reddit Keys"):
                if reddit_client_id:
                    save_api_key_to_env("REDDIT_CLIENT_ID", reddit_client_id)
                if reddit_client_secret:
                    save_api_key_to_env("REDDIT_CLIENT_SECRET", reddit_client_secret)
                st.success("✅ Saved Reddit keys to .env!")
                st.rerun()
        
        # GitHub
        st.markdown("**GitHub API**")
        github_token = st.text_input(
            "GitHub Token (Optional)",
            value=default_github_token,
            type="password",
            help="For higher rate limits"
        )
        
        if github_token and github_token != default_github_token:
            if st.button("💾 Save GitHub Token"):
                save_api_key_to_env("GITHUB_TOKEN", github_token)
                st.success("✅ Saved GitHub token to .env!")
                st.rerun()
        
        # Product Hunt
        st.markdown("**Product Hunt API**")
        ph_token = st.text_input(
            "Product Hunt Token (Optional)",
            value=default_ph_token,
            type="password"
        )
        
        if ph_token and ph_token != default_ph_token:
            if st.button("💾 Save Product Hunt Token"):
                save_api_key_to_env("PRODUCTHUNT_TOKEN", ph_token)
                st.success("✅ Saved Product Hunt token to .env!")
                st.rerun()
    
    
    st.sidebar.divider()
    
    # Data Sources Section
    with st.sidebar.expander("📊 Data Sources", expanded=True):
        st.markdown("**No Auth Required:**")
        use_hackernews = st.checkbox("Hacker News", value=True, help="✅ No API key required!")
        use_stackoverflow = st.checkbox("Stack Overflow", value=True, help="✅ No API key required!")
        use_pushshift = st.checkbox("Reddit (Pushshift)", value=False, help="✅ No auth, temporary until official API")
        
        # Auto-detect Reddit API availability
        has_reddit_api = bool(reddit_client_id and reddit_client_secret)
        if not has_reddit_api:
            use_reddit_rss = st.checkbox("Reddit (RSS - No API needed!)", value=True, help="✅ Works immediately without API keys")
        else:
            use_reddit_rss = False
        
        st.markdown("**Requires API Keys:**")
        use_reddit = st.checkbox("Reddit (Official)", value=False, help="⚠️ Requires API credentials")
        use_github = st.checkbox("GitHub Issues", value=False, help="⚙️ Optional token for higher limits")
        use_producthunt = st.checkbox("Product Hunt", value=False, help="⚠️ Requires API token")
        
        st.markdown("**Experimental:**")
        use_linkedin = st.checkbox("LinkedIn", value=False, help="⚠️ Experimental, may not work")
    
    st.sidebar.divider()
    
    # Search Settings
    st.sidebar.subheader("Search Settings")
    
    # NEW: Search Mode Selection
    search_mode = st.sidebar.radio(
        "Search Mode",
        ["Keyword Search", "Browse Top Posts"],
        help="Keyword: Search for specific terms. Browse: Get top posts from each source"
    )
    browse_mode = (search_mode == "Browse Top Posts")
    
    # Only show keyword input if in keyword mode
    if not browse_mode:
        keywords_input = st.sidebar.text_input(
            "Keywords (comma separated)", 
            "hate, manual, tedious, struggle, painful, hours, looking for, can't"
        )
    else:
        keywords_input = ""  # No keywords in browse mode
        st.sidebar.info("📖 Browse mode: Fetching top posts without keyword filtering")
    
    # Sort order
    sort_by = st.sidebar.selectbox(
        "Sort By",
        ["Hot", "New", "Top"],
        help="How to sort posts from each source"
    ).lower()
    
    subreddits_input = st.sidebar.text_input("Subreddits (comma separated)", "SaaS, Entrepreneur, smallbusiness, marketing")
    posts_per_source = st.sidebar.slider("Posts per Source", 10, 100, 20)
    
    run_search = st.sidebar.button("🚀 Start Hunting", type="primary")

    # --- Main Logic ---
    if run_search:
        if not openrouter_api_key:
            st.error("Please configure your OpenRouter API key in the sidebar or .env file.")
            return
        
        # Check if at least one source is enabled
        enabled_sources = [use_hackernews, use_stackoverflow, use_pushshift, use_reddit, use_github, use_producthunt, use_linkedin]
        if not any(enabled_sources):
            st.error("Please enable at least one data source.")
            return
        
        # Validate credentials for sources that need them
        if use_reddit and not (reddit_client_id and reddit_client_secret):
            st.error("Reddit (Official) is enabled but credentials are missing.")
            return
        if use_producthunt and not ph_token:
            st.error("Product Hunt is enabled but token is missing.")
            return

        # Initialize sources
        clean_subreddits = [s.strip() for s in subreddits_input.split(',')]
        clean_keywords = [k.strip() for k in keywords_input.split(',')]
        
        # Calculate posts per source
        num_sources = sum(enabled_sources)
        
        # 1. Scraping Phase (Parallel with Aggregator)
        with st.status("🔍 Scanning platforms in parallel...", expanded=True) as status:
            # Prepare sources for aggregator
            sources_to_fetch = []
            
            if use_hackernews:
                sources_to_fetch.append(("hackernews", HackerNewsSource()))
            
            if use_stackoverflow:
                sources_to_fetch.append(("stackoverflow", StackOverflowSource()))
            
            if use_pushshift:
                sources_to_fetch.append(("pushshift", RedditPushshiftSource()))
            
            if use_reddit:
                sources_to_fetch.append(("reddit", RedditSource(client_id=reddit_client_id, client_secret=reddit_client_secret)))
            
            # NEW: RSS fallback
            if 'use_reddit_rss' in locals() and use_reddit_rss:
                sources_to_fetch.append(("reddit_rss", RedditRSSSource()))
            
            if use_github:
                sources_to_fetch.append(("github", GitHubSource(token=github_token if github_token else None)))
            
            if use_producthunt:
                sources_to_fetch.append(("producthunt", ProductHuntSource(token=ph_token)))
            
            if use_linkedin:
                sources_to_fetch.append(("linkedin", LinkedInSource()))
            
            # Use aggregator for parallel fetching
            aggregator = Aggregator(max_workers=min(len(sources_to_fetch), 5))
            result = aggregator.fetch_from_sources(
                sources_to_fetch, 
                clean_keywords, 
                posts_per_source,
                browse_mode=browse_mode,
                sort_by=sort_by
            )
            
            all_posts = result['posts']
            errors = result['errors']
            fetch_stats = result['stats']
            
            # Display results
            st.write(f"📊 Total posts collected: {len(all_posts)}")
            st.write(f"✅ Successful: {fetch_stats['successful_fetches']}/{fetch_stats['total_fetches']} sources")
            
            # Show errors if any - ALWAYS EXPANDED if there are errors
            if errors:
                with st.expander(f"⚠️ Fetch Errors ({len(errors)} sources failed)", expanded=True):
                    st.warning("Some sources encountered errors. This is normal - the app continues with working sources.")
                    for source, error in errors.items():
                        st.error(f"**{source.upper()}**: {error}")
                        
                        # Provide helpful hints for common errors
                        if "authentication" in error.lower() or "401" in error or "403" in error:
                            st.info(f"💡 **{source}** needs API credentials. Add them to your `.env` file or disable this source.")
                        elif "rate limit" in error.lower() or "429" in error:
                            st.info(f"💡 **{source}** rate limit reached. Try again later or add API credentials for higher limits.")
                        elif "timeout" in error.lower():
                            st.info(f"💡 **{source}** timed out. The service might be slow - try again.")
            
            # Show fetch times
            if fetch_stats['fetch_times']:
                with st.expander("⏱️ Fetch Performance", expanded=False):
                    for source, fetch_time in fetch_stats['fetch_times'].items():
                        st.write(f"**{source.upper()}**: {fetch_time:.2f}s")
            
            # Enhanced empty results handling
            if not all_posts:
                status.update(label="No posts found", state="error")
                
                st.error("### 🔍 No Posts Found")
                st.write("**Possible reasons:**")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("""
                    **Source Issues:**
                    - All sources failed (check errors above)
                    - Sources need API keys
                    - Rate limits reached
                    """)
                
                with col2:
                    st.markdown("""
                    **Search Issues:**
                    - Keywords too specific
                    - No recent posts matching keywords
                    - Try broader terms like "manual", "tedious"
                    """)
                
                st.info("""
                **💡 Quick Fixes:**
                1. Enable **Hacker News** + **Stack Overflow** (work without API keys)
                2. Try keywords: `manual`, `tedious`, `hate`, `waste time`
                3. Check the errors above for specific source issues
                """)
                return
            
            # Deduplicate posts
            original_count = len(all_posts)
            all_posts = aggregator.deduplicate_posts(all_posts)
            duplicates_removed = original_count - len(all_posts)
            
            if duplicates_removed > 0:
                st.write(f"🔄 After deduplication: {len(all_posts)} unique posts ({duplicates_removed} duplicates removed)")
            else:
                st.write(f"🔄 After deduplication: {len(all_posts)} unique posts")
            
            status.update(label="Scraping Complete!", state="complete", expanded=False)

        # 2. Analysis Phase
        analyzer = Analyzer(api_key=openrouter_api_key)
        db = get_database()
        trend_analyzer = TrendAnalyzer(db)
        
        with st.spinner("🧠 AI Analyzer analyzing opportunities..."):
            try:
                analyzed_posts = analyzer.analyze_posts(all_posts)
                
                # Check for analysis failures
                failed_analyses = sum(1 for p in analyzed_posts if not p.get('analysis') or not isinstance(p.get('analysis'), dict))
                if failed_analyses > 0:
                    st.warning(f"⚠️ {failed_analyses}/{len(analyzed_posts)} posts failed AI analysis. This might be due to API rate limits or malformed posts.")
                
            except Exception as e:
                st.error(f"### ❌ AI Analysis Failed")
                st.error(f"**Error:** {str(e)}")
                st.info("""
                **Common causes:**
                - Invalid or missing OpenRouter API key
                - API rate limit exceeded
                - Network connectivity issues
                
                **Solutions:**
                1. Check your `OPENROUTER_API_KEY` in the sidebar
                2. Verify the API key at https://openrouter.ai/settings/keys
                3. Wait a few minutes if rate limited
                """)
                return
            
            # Save to database and track trends
            saved_count = 0
            for post in analyzed_posts:
                if db.save_post(post):
                    saved_count += 1
                if 'analysis' in post and isinstance(post['analysis'], dict):
                    db.save_analysis(post['id'], post['analysis'])
                    trend_analyzer.track_problem(post['id'], post['analysis'])
            
            if saved_count > 0:
                st.success(f"💾 Saved {saved_count} posts to database")

        # 3. Display Results
        display_results(analyzed_posts, db, trend_analyzer)

def display_results(posts, db: Database, trend_analyzer: TrendAnalyzer):
    st.divider()
    
    # Create tabs for Results, Trends, Stats, and Analytics
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Current Results", "📈 Trending Problems", "💾 Database Stats", "📉 Analytics"])
    
    with tab1:
        display_current_results(posts)
    
    with tab2:
        display_trends(db, trend_analyzer)
    
    with tab3:
        display_database_stats(db)
    
    with tab4:
        display_analytics(posts)

def display_current_results(posts):
    """Display current batch results with filters."""
    # Process data for display
    data = []
    for p in posts:
        analysis = p.get('analysis', {})
        # Skip if analysis failed or structure is weird
        if not isinstance(analysis, dict):
            continue
            
        is_pain = analysis.get('is_pain_point', False)
        score = analysis.get('score', 0)
        
        if is_pain: # Only show validated pain points by default
            data.append({
                "Score": score,
                "Title": p['title'],
                "Source": p.get('source', 'unknown'),
                "Solution Pitch": analysis.get('solution', 'N/A'),
                "Reasoning": analysis.get('reasoning', 'N/A'),
                "Trend": analysis.get('trend_score', 0),
                "Market Size": analysis.get('market_size', 'unknown'),
                "Competitors": analysis.get('competitors', 'unknown'),
                "Difficulty": analysis.get('difficulty', 0),
                "Time to Build": analysis.get('time_to_build', 'N/A'),
                "Link": p['url'],
                "Full Text": p.get('text', ''),
                "Raw Data": p # Keep full object for details
            })

    if not data:
        st.info("### 🔍 No Validated Pain Points Found")
        
        # Show how many posts were analyzed
        total_analyzed = len(posts)
        st.write(f"**Analyzed {total_analyzed} posts, but none were identified as strong pain points.**")
        
        st.markdown("""
        **This could mean:**
        - The AI didn't find clear pain points in the posts
        - Posts were too vague or not business-focused
        - Keywords didn't match pain point discussions
        
        **💡 Try these improvements:**
        1. **Better keywords**: Use `hate`, `manual`, `tedious`, `waste time`, `frustrated`
        2. **Enable more sources**: Hacker News + Stack Overflow work great
        3. **Lower filters**: Reduce min score to see marginal ideas
        4. **Different subreddits**: Try r/SaaS, r/Entrepreneur, r/productivity
        
        **Debug Info:**
        - Posts collected: {total_analyzed}
        - Pain points found: 0
        - Check the Analytics tab to see what was analyzed
        """)
        return

    df = pd.DataFrame(data)
    
    # Filters Section
    st.subheader("🔍 Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_score = st.slider("Min Score", 0, 10, 0, key="filter_min_score")
    
    with col2:
        market_sizes = ['All'] + list(df['Market Size'].unique())
        selected_market = st.selectbox("Market Size", market_sizes, key="filter_market")
    
    with col3:
        sources = ['All'] + list(df['Source'].unique())
        selected_source = st.selectbox("Source", sources, key="filter_source")
    
    # Apply filters
    filtered_df = df[df['Score'] >= min_score]
    
    if selected_market != 'All':
        filtered_df = filtered_df[filtered_df['Market Size'] == selected_market]
    
    if selected_source != 'All':
        filtered_df = filtered_df[filtered_df['Source'] == selected_source]
    
    filtered_df = filtered_df.sort_values(by="Score", ascending=False)
    
    if len(filtered_df) == 0:
        st.warning("No results match your filters. Try adjusting them.")
        return

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Scanned", len(posts))
    col2.metric("Validated Ideas", len(df))
    col3.metric("After Filters", len(filtered_df))
    col4.metric("Avg Difficulty", f"{filtered_df['Difficulty'].mean():.1f}/10")

    # Main Table
    st.subheader("🏆 Top Opportunities")
    
    # Enhanced table with new fields
    st.dataframe(
        filtered_df[['Score', 'Trend', 'Title', 'Market Size', 'Difficulty', 'Time to Build', 'Source']],
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Viability",
                help="AI Score 1-10",
                format="%d",
                min_value=0,
                max_value=10,
            ),
            "Trend": st.column_config.ProgressColumn(
                "Trend 📈",
                help="How trending/emerging (1-10)",
                format="%d",
                min_value=0,
                max_value=10,
            ),
            "Difficulty": st.column_config.ProgressColumn(
                "Build Difficulty",
                help="Technical complexity (1-10)",
                format="%d",
                min_value=0,
                max_value=10,
            ),
        },
        hide_index=True
    )

    # Detailed Cards
    st.subheader("📝 Detailed Analysis")
    for _, row in filtered_df.iterrows():
        # Color code by score
        if row['Score'] >= 8:
            emoji = "🔥"
        elif row['Score'] >= 6:
            emoji = "⭐"
        else:
            emoji = "💡"
            
        with st.expander(f"{emoji} [{row['Score']}/10] {row['Title']}"):
            # Top metrics row
            metric_cols = st.columns(5)
            metric_cols[0].metric("Trend Score", f"{row['Trend']}/10")
            metric_cols[1].metric("Market Size", row['Market Size'].title())
            metric_cols[2].metric("Difficulty", f"{row['Difficulty']}/10")
            metric_cols[3].metric("Time to Build", row['Time to Build'])
            metric_cols[4].metric("Source", row['Source'].upper())
            
            st.divider()
            
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"**💡 AI Solution:**\n> {row['Solution Pitch']}")
                st.markdown(f"**🤔 Reasoning:** {row['Reasoning']}")
                st.markdown(f"**🏢 Competitors:** {row['Competitors']}")
                st.markdown("**Original Post:**")
                st.info(row['Full Text'][:500] + "..." if len(row['Full Text']) > 500 else row['Full Text'])
            with c2:
                st.link_button("🔗 View Source", row['Link'])
                st.json(row['Raw Data']['analysis'])

    # Export
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download Research Data (CSV)",
        csv,
        "problem_hunter_results.csv",
        "text/csv",
        key='download-csv'
    )

def display_trends(db: Database, trend_analyzer: TrendAnalyzer):
    """Display trending problems over time."""
    st.subheader("📈 Trending Problems")
    st.markdown("Problems appearing frequently across multiple scans")
    
    # Time range selector
    col1, col2 = st.columns(2)
    with col1:
        days = st.selectbox("Time Range", [7, 14, 30, 90], index=1, key="trend_days")
    with col2:
        min_occurrences = st.slider("Min Occurrences", 2, 10, 3, key="min_occ")
    
    # Get emerging trends
    st.markdown("### 🚀 Emerging Trends")
    emerging = trend_analyzer.get_emerging_trends(days=days, min_recent=min_occurrences)
    
    if emerging:
        for trend in emerging[:10]:  # Top 10
            with st.expander(f"⭐ {trend['problem_summary'][:100]}... (Score: {trend['avg_score']:.1f})"):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Occurrences", trend['occurrence_count'])
                col2.metric("Avg Score", f"{trend['avg_score']:.1f}/10")
                col3.metric("Recent Activity", trend.get('recent_count', 0))
                col4.metric("Status", trend.get('status', 'unknown').upper())
                
                st.markdown(f"**Sources:** {trend.get('sources', 'N/A')}")
                st.markdown(f"**First Seen:** {trend.get('first_seen', 'N/A')}")
                st.markdown(f"**Last Seen:** {trend.get('last_seen', 'N/A')}")
    else:
        st.info("No emerging trends found. Run more scans to build trend data!")
    
    # Get declining trends
    st.markdown("### 📉 Declining Trends")
    declining = trend_analyzer.get_declining_trends(days=days)
    
    if declining:
        for trend in declining[:5]:  # Top 5
            with st.expander(f"📉 {trend['problem_summary'][:100]}..."):
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Occurrences", trend['occurrence_count'])
                col2.metric("Past Activity", trend.get('past_count', 0))
                col3.metric("Recent Activity", trend.get('recent_count', 0))
                
                st.markdown(f"**Sources:** {trend.get('sources', 'N/A')}")
    else:
        st.info("No declining trends detected.")

def display_database_stats(db: Database):
    """Display database statistics."""
    st.subheader("💾 Database Statistics")
    
    stats = db.get_stats()
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Posts", stats.get('total_posts', 0))
    col2.metric("Total Analyses", stats.get('total_analyses', 0))
    col3.metric("Pain Points Found", stats.get('pain_points_found', 0))
    col4.metric("Avg Pain Score", stats.get('avg_pain_score', 0))
    
    # Posts by source
    st.markdown("### Posts by Source")
    if stats.get('posts_by_source'):
        source_df = pd.DataFrame([
            {"Source": k.upper(), "Count": v} 
            for k, v in stats['posts_by_source'].items()
        ])
        st.bar_chart(source_df.set_index('Source'))
    else:
        st.info("No data yet. Run a scan to populate the database!")

def display_analytics(posts):
    """Display analytics dashboard with visualizations."""
    st.subheader("📉 Analytics Dashboard")
    
    # Process data
    data = []
    for p in posts:
        analysis = p.get('analysis', {})
        if not isinstance(analysis, dict):
            continue
        
        is_pain = analysis.get('is_pain_point', False)
        if is_pain:
            data.append({
                "Score": analysis.get('score', 0),
                "Trend": analysis.get('trend_score', 0),
                "Market Size": analysis.get('market_size', 'unknown'),
                "Difficulty": analysis.get('difficulty', 0),
                "Source": p.get('source', 'unknown'),
                "Title": p['title']
            })
    
    if not data:
        st.info("No data to visualize. Run a scan first!")
        return
    
    df = pd.DataFrame(data)
    
    # Row 1: Market Size Distribution & Difficulty vs Opportunity
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Market Size Distribution")
        market_counts = df['Market Size'].value_counts()
        
        # Create pie chart data
        pie_data = pd.DataFrame({
            'Market Size': market_counts.index,
            'Count': market_counts.values
        })
        
        # Display as bar chart (Streamlit native)
        st.bar_chart(pie_data.set_index('Market Size'))
        
        # Show percentages
        total = len(df)
        for market, count in market_counts.items():
            pct = (count / total) * 100
            st.write(f"**{market.title()}**: {count} ({pct:.1f}%)")
    
    with col2:
        st.markdown("### 🎯 Difficulty vs Opportunity Matrix")
        st.markdown("*Higher score + lower difficulty = better opportunity*")
        
        # Create scatter plot data
        scatter_df = df[['Difficulty', 'Score', 'Title']].copy()
        scatter_df['Opportunity Score'] = scatter_df['Score'] - (scatter_df['Difficulty'] * 0.5)
        
        # Color code by opportunity score
        scatter_df['Color'] = scatter_df['Opportunity Score'].apply(
            lambda x: '🔥 High' if x >= 7 else ('⭐ Medium' if x >= 5 else '💡 Low')
        )
        
        # Display top opportunities
        top_opps = scatter_df.nlargest(5, 'Opportunity Score')
        st.markdown("**Top 5 Opportunities (High Score, Low Difficulty):**")
        for idx, row in top_opps.iterrows():
            st.write(f"{row['Color']}: **{row['Title'][:60]}...** (Score: {row['Score']}, Diff: {row['Difficulty']})")
    
    # Row 2: Source Breakdown
    st.markdown("### 📱 Results by Source")
    
    # Create tabs for each source
    sources = df['Source'].unique()
    source_tabs = st.tabs([s.upper() for s in sources])
    
    for idx, source in enumerate(sources):
        with source_tabs[idx]:
            source_df = df[df['Source'] == source]
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total", len(source_df))
            col2.metric("Avg Score", f"{source_df['Score'].mean():.1f}")
            col3.metric("Avg Difficulty", f"{source_df['Difficulty'].mean():.1f}")
            
            # Top 3 from this source
            st.markdown("**Top 3 Problems:**")
            top_3 = source_df.nlargest(3, 'Score')
            for _, row in top_3.iterrows():
                st.write(f"⭐ **[{row['Score']}/10]** {row['Title'][:80]}...")
    
    # Row 3: Score Distribution
    st.markdown("### 📈 Score Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Score histogram
        score_counts = df['Score'].value_counts().sort_index()
        st.bar_chart(score_counts)
    
    with col2:
        # Statistics
        st.markdown("**Statistics:**")
        st.write(f"- **Mean Score**: {df['Score'].mean():.2f}")
        st.write(f"- **Median Score**: {df['Score'].median():.0f}")
        st.write(f"- **Std Dev**: {df['Score'].std():.2f}")
        st.write(f"- **High Scores (8+)**: {len(df[df['Score'] >= 8])}")
        st.write(f"- **Medium Scores (6-7)**: {len(df[(df['Score'] >= 6) & (df['Score'] < 8)])}")
        st.write(f"- **Low Scores (<6)**: {len(df[df['Score'] < 6])}")

if __name__ == "__main__":
    main()
