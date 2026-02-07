# 🎯 Problem Hunter

**AI-Powered Multi-Platform Opportunity Discovery Engine**

Scan 7+ data sources (Hacker News, Stack Overflow, GitHub, Reddit, Product Hunt) to discover validated micro-SaaS opportunities with advanced AI analysis.

---

## ✨ Features

### 🌐 Multi-Source Data Collection
- **Hacker News** - Comments & discussions (✅ No auth required)
- **Stack Overflow** - Unanswered questions (✅ No auth required)
- **Reddit (Pushshift)** - Alternative Reddit source (✅ No auth required)
- **Reddit (Official)** - Official API (requires credentials)
- **GitHub Issues** - Feature requests & enhancements (optional token)
- **Product Hunt** - Pain points from comments (requires token)
- **LinkedIn** - Experimental (placeholder)

### 🧠 Advanced AI Analysis
Powered by Google Gemini with **5 analysis dimensions**:

| Dimension | Description |
|-----------|-------------|
| **Viability Score** (1-10) | Overall opportunity quality |
| **Trend Score** (1-10) | How trending/emerging the problem is |
| **Market Size** | Estimated TAM (large/medium/small) |
| **Competitors** | List of 1-3 existing solutions |
| **Difficulty** (1-10) | Technical complexity to build MVP |
| **Time to Build** | Estimated dev time (1-2 weeks to 6+ months) |

### 🎨 Rich UI
- 🔥 Score-based emojis (🔥 8+, ⭐ 6+, 💡 <6)
- 📊 Interactive metrics dashboard
- 📈 Progress bars for scores and trends
- 🏷️ Source badges (HN, SO, GITHUB, etc.)
- 💾 CSV export with all analysis fields

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
git clone https://github.com/vjwork100-hash/problem_hunter.git
cd problem_hunter
pip install -r requirements.txt
```

### 2. Configure API Keys

**Required:**
```bash
GOOGLE_API_KEY=your_gemini_api_key
```

**Optional (enable more sources):**
```bash
# Reddit Official API
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# GitHub (higher rate limits)
GITHUB_TOKEN=your_github_token

# Product Hunt
PRODUCTHUNT_TOKEN=your_producthunt_token
```

Copy `.env.example` to `.env` and add your keys.

### 3. Run
```bash
streamlit run app.py
```

### 4. Start Hunting!
1. **Enable sources** (HN + SO work immediately, no auth!)
2. **Add Gemini API key** in sidebar
3. **Configure keywords** (hate, manual, tedious, struggle, etc.)
4. **Click "Start Hunting"**

---

## 📊 Example Output

```json
{
  "is_pain_point": true,
  "score": 9,
  "solution": "StripeSync: Auto-sync Stripe to QuickBooks with AI categorization",
  "reasoning": "High frequency (weekly), clear workflow pain, B2B context",
  "trend_score": 6,
  "market_size": "medium",
  "competitors": "Zapier, Automate.io",
  "difficulty": 4,
  "time_to_build": "1-2 months"
}
```

---

## 🏗️ Architecture

```
problem_hunter/
├── sources/
│   ├── base_source.py          # Abstract interface
│   ├── hackernews_source.py    # ✅ No auth
│   ├── stackoverflow_source.py # ✅ No auth
│   ├── reddit_pushshift.py     # ✅ No auth
│   ├── reddit_source.py        # ⚠️ Requires API
│   ├── github_source.py        # ⚙️ Optional token
│   ├── producthunt_source.py   # ⚠️ Requires token
│   └── linkedin_source.py      # ⚠️ Experimental
├── analyzer.py                 # Enhanced AI with 5 dimensions
├── app.py                      # Multi-source Streamlit UI
├── cache.py                    # Result caching
└── requirements.txt
```

---

## 🎯 Use Cases

- **Solo Developers**: Find validated micro-SaaS ideas
- **Market Researchers**: Identify emerging pain points
- **Product Managers**: Discover feature gaps
- **Entrepreneurs**: Validate business ideas with real data

---

## 🛡️ Privacy & Ethics

- **Read-only**: No posting, commenting, or voting
- **Public data only**: Only analyzes publicly visible content
- **No redistribution**: Data not shared or sold
- **Rate limited**: Respects all API limits
- **Local caching**: Minimizes redundant API calls
- **Educational use**: Non-commercial research

---

## 🔧 Technical Stack

- **Python 3.10+**
- **Streamlit** - Interactive web UI
- **Google Gemini** - AI analysis
- **PRAW** - Reddit API
- **Requests** - HTTP client for APIs
- **Pandas** - Data processing

---

## 📝 API Requirements

| Source | Auth Required | Rate Limit | Notes |
|--------|---------------|------------|-------|
| Hacker News | ❌ No | None | Algolia API |
| Stack Overflow | ❌ No | 300/day | Stack Exchange API |
| Pushshift | ❌ No | ~200/min | Reddit alternative |
| Reddit Official | ✅ Yes | 60/min | OAuth2 required |
| GitHub | ⚙️ Optional | 60/hr (5000 with token) | Higher limits with PAT |
| Product Hunt | ✅ Yes | Unknown | GraphQL API |

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional data sources
- Enhanced AI prompts
- Trend detection (SQLite tracking)
- Analytics dashboard (charts)
- Better filtering/export

---

## 📄 License

MIT License - See LICENSE file for details

---

## ⚠️ Disclaimer

This tool is for educational and research purposes only. All data accessed is publicly available. Users are responsible for complying with each platform's API Terms of Service.

---

## 🔗 Resources

- [Reddit API Documentation](https://www.reddit.com/dev/api/)
- [Hacker News API](https://hn.algolia.com/api)
- [Stack Exchange API](https://api.stackexchange.com/)
- [GitHub API](https://docs.github.com/en/rest)
- [Product Hunt API](https://api.producthunt.com/v2/docs)
