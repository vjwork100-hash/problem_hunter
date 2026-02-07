# Problem Hunter - Quick Setup Guide

## 🚀 Getting Started

### 1. Required API Key
**Google Gemini API** (Required for AI analysis)
- Get it here: https://ai.google.dev/
- Add to `.env`: `GOOGLE_API_KEY=your_key_here`

### 2. Optional API Keys (Enable More Sources)

#### Reddit Official API (Optional - Pushshift works without this!)
```bash
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=ProblemHunter/0.1
```
Get from: https://www.reddit.com/prefs/apps

#### GitHub (Optional - Higher rate limits)
```bash
GITHUB_TOKEN=your_personal_access_token
```
Get from: https://github.com/settings/tokens

#### Product Hunt (Optional)
```bash
PRODUCTHUNT_TOKEN=your_token
```
Get from: https://api.producthunt.com/v2/docs

### 3. LinkedIn - NO API KEY NEEDED (But Doesn't Work)
**LinkedIn is experimental and currently returns no results** because:
- LinkedIn actively blocks web scrapers
- Official LinkedIn API requires partnership (not publicly available)
- It's included as a placeholder for future implementation

**Recommendation**: Disable LinkedIn source in the UI - it won't find anything.

### 4. Sources That Work Immediately (No Auth Required!)
✅ **Hacker News** - Always works, no setup
✅ **Stack Overflow** - Always works, no setup  
✅ **Pushshift Reddit** - Always works, no setup (Reddit alternative)

### 5. Expanded Subreddit Coverage
Now searching **35+ subreddits** including:
- Entrepreneur, smallbusiness, startups, SideProject
- SaaS, microsaas, indiehackers
- productivity, freelance, digitalnomad
- Accounting, Bookkeeping, personalfinance
- marketing, sales, SEO, ecommerce
- And many more!

## 💡 Tips for Better Results

### Use Better Keywords
Instead of generic terms, try:
- **Pain-focused**: "hate", "tedious", "manual", "waste time", "struggle"
- **Frequency**: "every day", "every week", "constantly"
- **Emotion**: "frustrated", "annoying", "broken", "sucks"

### Enable Multiple Sources
- Start with **HN + SO + Pushshift** (no auth needed)
- Add Reddit Official + GitHub if you have API keys
- Skip LinkedIn (doesn't work)

### Adjust Filters
- Lower min score to see more results
- Try different market sizes
- Check multiple sources

### Run Multiple Scans
- Try different keyword combinations
- Scan at different times
- Build trend data over days/weeks

## 🔧 Quick Troubleshooting

**No results found?**
1. Check that Gemini API key is set
2. Try broader keywords ("manual", "tedious")
3. Enable Hacker News + Stack Overflow (always work)
4. Lower the min score filter

**LinkedIn not working?**
- This is expected! LinkedIn blocks scrapers
- Disable it in the UI
- Use other sources instead

**Reddit not working?**
- Use Pushshift instead (no auth required)
- Or add Reddit API credentials to .env
