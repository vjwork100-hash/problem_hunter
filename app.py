import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from sources.reddit_source import RedditSource
from sources.hackernews_source import HackerNewsSource
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
    st.markdown("Scan multiple platforms for validated pain points and get instant micro-SaaS solutions.")

    # --- Sidebar Configuration ---
    with st.sidebar:
        st.header("Configuration")
        
        # Data Sources Section
        with st.expander("📊 Data Sources", expanded=True):
            use_hackernews = st.checkbox("Hacker News", value=True, help="✅ No API key required!")
            use_reddit = st.checkbox("Reddit", value=False, help="⚠️ Requires API credentials")
        
        # API Keys Section
        with st.expander("🔑 API Keys", expanded=False):
            reddit_client_id = st.text_input("Reddit Client ID", value=os.getenv("REDDIT_CLIENT_ID", ""), type="password")
            reddit_client_secret = st.text_input("Reddit Client Secret", value=os.getenv("REDDIT_CLIENT_SECRET", ""), type="password")
            google_api_key = st.text_input("Gemini API Key", value=os.getenv("GOOGLE_API_KEY", ""), type="password")
            
            if not google_api_key:
                st.warning("⚠️ Gemini API key required for analysis.")
            if use_reddit and not (reddit_client_id and reddit_client_secret):
                st.warning("⚠️ Reddit credentials required if Reddit is enabled.")

        st.divider()
        
        # Search Settings
        st.subheader("Search Settings")
        subreddits_input = st.text_input("Subreddits (comma separated)", "SaaS, Entrepreneur, smallbusiness, marketing")
        keywords_input = st.text_input("Keywords (comma separated)", "hate, manual, tedious, struggle, painful")
        max_posts = st.slider("Max Posts to Analyze", 10, 100, 20)
        
        run_search = st.button("🚀 Start Hunting", type="primary")

    # --- Main Logic ---
    if run_search:
        if not google_api_key:
            st.error("Please configure your Gemini API key in the sidebar or .env file.")
            return
        
        if not use_hackernews and not use_reddit:
            st.error("Please enable at least one data source.")
            return
        
        if use_reddit and not (reddit_client_id and reddit_client_secret):
            st.error("Reddit is enabled but credentials are missing.")
            return

        # Initialize sources
        clean_subreddits = [s.strip() for s in subreddits_input.split(',')]
        clean_keywords = [k.strip() for k in keywords_input.split(',')]
        
        all_posts = []
        
        # 1. Scraping Phase
        with st.status("🔍 Scanning platforms...", expanded=True) as status:
            if use_hackernews:
                st.write("📰 Fetching from Hacker News...")
                try:
                    hn_source = HackerNewsSource()
                    hn_posts = hn_source.fetch_posts(clean_keywords, limit=max_posts//2 if use_reddit else max_posts)
                    all_posts.extend(hn_posts)
                    st.write(f"✅ Found {len(hn_posts)} HN posts")
                except Exception as e:
                    st.write(f"❌ HN Error: {e}")
            
            if use_reddit:
                st.write("🤖 Fetching from Reddit...")
                try:
                    reddit_source = RedditSource(client_id=reddit_client_id, client_secret=reddit_client_secret)
                    reddit_posts = reddit_source.fetch_posts(clean_keywords, limit=max_posts//2 if use_hackernews else max_posts, subreddits=clean_subreddits)
                    all_posts.extend(reddit_posts)
                    st.write(f"✅ Found {len(reddit_posts)} Reddit posts")
                except Exception as e:
                    st.write(f"❌ Reddit Error: {e}")
            
            st.write(f"📊 Total posts collected: {len(all_posts)}")
            
            if not all_posts:
                status.update(label="No relevant posts found.", state="error")
                return
            
            status.update(label="Scraping Complete!", state="complete", expanded=False)

        # 2. Analysis Phase
        analyzer = Analyzer(api_key=google_api_key)
        with st.spinner("🧠 AI Analyzer analyzing opportunities..."):
            analyzed_posts = analyzer.analyze_posts(all_posts)

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
