import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from sources.reddit_source import RedditSource
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
    st.title("🎯 Problem Hunter")
    st.markdown("*AI-Powered Multi-Platform Opportunity Discovery Engine*")
    
    # Sidebar Configuration
    st.sidebar.header("⚙️ Configuration")
    
    # API Keys Section
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
