# Problem Hunter

**Problem Hunter** is an AI-powered research tool that scans Reddit for business problems and proposes micro-SaaS solutions.

## 🚀 Quick Start

### 1. Requirements
You need two things:
1.  **Reddit API**: Go to [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps), create a "script" app. Note the `client_id` (under the name) and `client_secret`.
2.  **Gemini API**: Get your key from [Google AI Studio](https://aistudio.google.com/).

### 2. Setup Environment
Rename `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
# Edit .env with your keys
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the App
```bash
streamlit run app.py
```

## 🎯 How to Use

1.  **Sidebar Config**: Check your API keys are loaded.
2.  **Define Scope**:
    *   **Subreddits**: Comma-separated list (e.g., `SaaS, Entrepreneur, marketing`).
    *   **Keywords**: Pain indicators (e.g., `hate, manual, struggle`).
    *   **Max Posts**: Start low (e.g., 20) to save API quota.
3.  **Start Hunting**: Click **[🚀 Start Hunting]**.
    *   The app will first scan Reddit and filter for "pain" keywords.
    *   Then, Gemini will analyze the filtered posts in batches.
4.  **Review Results**:
    *   **Score (1-10)**: Higher is better. Focus on 8+.
    *   **Solution Pitch**: Read the AI's proposed micro-SaaS idea.
    *   **Deep Dive**: Expand a row to see the full original post and reasoning.
5.  **Export**: Click "Download Research Data" to save your validated ideas.

## 🧠 Key Features
*   **Regex Pre-filter**: We only send "high signal" posts to the AI to save money.
*   **Smart Caching**: Fetched posts and Analysis results are cached in the `cache/` folder. Re-running the same search is instant!
*   **Structured AI**: Gemini returns a JSON with validation, scoring, and a specific solution pitch.
