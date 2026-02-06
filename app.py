import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from scraper import RedditClient
from analyzer import Analyzer

# Page Config
st.set_page_config(
    page_title="Problem Hunter",
    page_icon="🎯",
    layout="wide"
)

# Load Environment Variables
load_dotenv()

def main():
    st.title("🎯 Problem Hunter: AI SaaS Opportunity Finder")
    st.markdown("Scan Reddit for validated pain points and get instant micro-SaaS solutions.")

    # --- Sidebar Configuration ---
    with st.sidebar:
        st.header("Configuration")
        
        # API Keys Section
        with st.expander("API Keys", expanded=False):
            reddit_client_id = st.text_input("Reddit Client ID", value=os.getenv("REDDIT_CLIENT_ID", ""), type="password")
            reddit_client_secret = st.text_input("Reddit Client Secret", value=os.getenv("REDDIT_CLIENT_SECRET", ""), type="password")
            google_api_key = st.text_input("Gemini API Key", value=os.getenv("GOOGLE_API_KEY", ""), type="password")
            
            if not (reddit_client_id and reddit_client_secret and google_api_key):
                st.warning("⚠️ Please provide all API keys to proceed.")

        st.divider()
        
        # Search Settings
        st.subheader("Search Settings")
        subreddits_input = st.text_input("Subreddits (comma separated)", "SaaS, Entrepreneur, smallbusiness, marketing")
        keywords_input = st.text_input("Keywords (comma separated)", "hate, manual, tedious, struggle, painful")
        max_posts = st.slider("Max Posts to Analyze", 10, 100, 20)
        
        run_search = st.button("🚀 Start Hunting", type="primary")

    # --- Main Logic ---
    if run_search:
        if not (reddit_client_id and reddit_client_secret and google_api_key):
            st.error("Please configure your API keys in the sidebar or .env file.")
            return

        # Initialize Clients
        clean_subreddits = [s.strip() for s in subreddits_input.split(',')]
        clean_keywords = [k.strip() for k in keywords_input.split(',')]
        
        client = RedditClient(client_id=reddit_client_id, client_secret=reddit_client_secret)
        analyzer = Analyzer(api_key=google_api_key)

        # 1. Scraping Phase
        with st.status("🔍 Scanning Reddit...", expanded=True) as status:
            st.write(f"Searching in: {', '.join(clean_subreddits)}")
            posts = client.fetch_posts(clean_subreddits, clean_keywords, limit=max_posts)
            st.write(f"Found {len(posts)} posts matching pain patterns.")
            
            if not posts:
                status.update(label="No relevant posts found.", state="error")
                return
            
            status.update(label="Scraping Complete!", state="complete", expanded=False)

        # 2. Analysis Phase
        with st.spinner("🧠 AI Analyzer analyzing opportunities..."):
            analyzed_posts = analyzer.analyze_posts(posts)

        # 3. Display Results
        display_results(analyzed_posts)

def display_results(posts):
    st.divider()
    
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
                "Subreddit": p['subreddit'],
                "Solution Pitch": analysis.get('solution', 'N/A'),
                "Reasoning": analysis.get('reasoning', 'N/A'),
                "Link": p['url'],
                "Full Text": p['text'],
                "Raw Data": p # Keep full object for details
            })

    if not data:
        st.info("No validated pain points found in this batch. Try broader keywords!")
        return

    df = pd.DataFrame(data)
    df = df.sort_values(by="Score", ascending=False)

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Scanned", len(posts))
    col2.metric("Validated Ideas", len(df))
    col3.metric("Top Opportunity Score", df['Score'].max())

    # Main Table
    st.subheader("🏆 Top Opportunities")
    
    # Simple table first
    st.dataframe(
        df[['Score', 'Title', 'Solution Pitch', 'Subreddit']],
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Viability Score",
                help="AI Score 1-10",
                format="%d",
                min_value=0,
                max_value=10,
            ),
            "Link": st.column_config.LinkColumn("Source")
        },
        hide_index=True
    )

    # Detailed Cards
    st.subheader("📝 Detailed Analysis")
    for _, row in df.iterrows():
        with st.expander(f"[{row['Score']}/10] {row['Title']}"):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"**💡 AI Solution:**\n> {row['Solution Pitch']}")
                st.markdown(f"**🤔 Reasoning:** {row['Reasoning']}")
                st.markdown("**Original Post:**")
                st.info(row['Full Text'][:500] + "..." if len(row['Full Text']) > 500 else row['Full Text'])
            with c2:
                st.link_button("View on Reddit", row['Link'])
                st.json(row['Raw Data']['analysis'])

    # Export
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download Research Data (CSV)",
        csv,
        "problem_hunter_results.csv",
        "text/csv",
        key='download-csv'
    )

if __name__ == "__main__":
    main()
