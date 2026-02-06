# Problem Hunter

An educational research tool for studying pain point discussions in business-focused Reddit communities.

## 📚 Purpose

This is a **learning project** exploring:
- Natural language processing for sentiment analysis
- Market research methodologies
- Pattern recognition in community discussions

Results are used to understand how online communities discuss workflow challenges and identify common themes.

## 🔍 How It Works

1. **Read-Only Access**: Searches public posts in business subreddits
2. **Pattern Analysis**: Uses AI to identify recurring workflow problems
3. **Local Processing**: All analysis happens locally, no data redistribution

## 🎯 Target Communities

Focuses on public business/entrepreneurship subreddits where users actively discuss workflow challenges:
- r/Entrepreneur
- r/smallbusiness
- r/SaaS
- r/startups
- r/marketing
- r/freelance

## 🛡️ Privacy & Ethics

- **Read-only**: No posting, commenting, or voting
- **Public data only**: Only analyzes publicly visible posts
- **No redistribution**: Data not shared, sold, or redistributed
- **Rate limited**: Respects Reddit API limits (<60 requests/minute)
- **Local storage**: Caches results locally for deduplication only
- **Educational use**: Non-commercial research and learning

## 🔧 Technical Stack

- **Python 3.10+**
- **PRAW**: Reddit API wrapper for read-only access
- **Google Gemini**: AI analysis for pattern recognition
- **Streamlit**: Simple web interface
- **Local caching**: SQLite for minimizing redundant API calls

## 📊 API Usage

- **Volume**: <1,000 requests per day
- **Rate**: <60 requests per minute
- **Scope**: Public posts only, no private/restricted content
- **Authentication**: Standard OAuth2 via PRAW

## 🚀 Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys (create .env file)
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT=ProblemHunter/1.0
GOOGLE_API_KEY=your_gemini_key

# Run
streamlit run app.py
```

## 📝 How to Use

1. Enter subreddits to search (comma-separated)
2. Add pain point keywords (e.g., "manual", "time-consuming")
3. Set max posts limit
4. Click "Start Hunting"
5. Review AI-analyzed results
6. Export to CSV for further study

## 🤝 Contributing

This is an educational project. Contributions welcome for:
- Improved pattern detection
- Better sentiment analysis
- Code optimization
- Documentation

## 📄 License

MIT License - See LICENSE file for details

## ⚠️ Disclaimer

This tool is for educational and research purposes only. All data accessed is publicly available on Reddit. Users are responsible for complying with Reddit's API Terms of Service and using the tool ethically.

## 🔗 Resources

- [Reddit API Documentation](https://www.reddit.com/dev/api/)
- [PRAW Documentation](https://praw.readthedocs.io/)
- [Reddit's Responsible Builder Policy](https://www.redditinc.com/policies/data-api-terms)
