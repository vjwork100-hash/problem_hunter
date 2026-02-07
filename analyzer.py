from google import genai
from google.genai import types
import os
import json
import time
from typing import List, Dict, Any
from dotenv import load_dotenv
from cache import Cache

class Analyzer:
    def __init__(self, api_key: str = None):
        load_dotenv()
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        self.cache = Cache()

    def analyze_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze a batch of posts using Gemini.
        Returns the original posts with added 'analysis' field.
        """
        if not self.api_key:
            return [{"error": "Missing Gemini API Key", **post} for post in posts]

        analyzed_posts = []
        posts_to_analyze = []

        # Check cache first
        for post in posts:
            cached_analysis = self.cache.get_analysis(post['id'])
            if cached_analysis:
                post['analysis'] = cached_analysis
                analyzed_posts.append(post)
            else:
                posts_to_analyze.append(post)

        if not posts_to_analyze:
            return analyzed_posts

        # Process new posts in small batches to avoid huge prompts/timeouts
        BATCH_SIZE = 5
        for i in range(0, len(posts_to_analyze), BATCH_SIZE):
            batch = posts_to_analyze[i:i+BATCH_SIZE]
            try:
                batch_results = self._call_gemini_batch(batch)
                
                # Validate batch results length matches input
                if len(batch_results) != len(batch):
                    print(f"Warning: Expected {len(batch)} results, got {len(batch_results)}")
                    # Pad with error objects if needed
                    while len(batch_results) < len(batch):
                        batch_results.append({"error": "Missing result from API", "is_pain_point": False, "score": 0})
                
                # Merge results back
                for post, analysis in zip(batch, batch_results):
                    post['analysis'] = analysis
                    # Save to cache if valid
                    if 'error' not in analysis:
                        self.cache.save_analysis(post['id'], analysis)
                    analyzed_posts.append(post)
                
                # Simple rate limit prevention
                time.sleep(1) 
                
            except Exception as e:
                print(f"Batch analysis failed: {e}")
                # Append failed posts with error
                for post in batch:
                    post['analysis'] = {"error": str(e), "is_pain_point": False, "score": 0}
                    analyzed_posts.append(post)

        return analyzed_posts

    def _call_gemini_batch(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Constructs a single prompt for a batch of posts and parses the JSON response.
        """
        
        posts_text = []
        for idx, post in enumerate(posts):
            content = (post.get('title', '') + "\n" + post.get('text', ''))[:1000] # Truncate for safety
            posts_text.append(f"POST_ID_{idx}:\n{content}\n---")
        
        joined_posts = "\n".join(posts_text)

        prompt = f"""
        You are a SaaS Product Researcher analyzing posts for software business opportunities.

        CRITICAL RULES:
        - Only mark as pain point if it's a REPEATABLE WORKFLOW problem (not one-off complaints)
        - Must be solvable by software (not human service/physical work)
        - Must indicate willingness to pay (time-consuming, business context, frequency mentioned)

        SCORING GUIDE (1-10):
        - 9-10: Repeated frequently ("every week"), clear workflow, B2B context, high frustration
        - 7-8: Clear automation opportunity, some frequency indicators, measurable pain
        - 4-6: Valid problem but niche/unclear market size
        - 1-3: Vague complaint, one-off issue, or already solved by existing tools

        NEW ANALYSIS DIMENSIONS:
        
        1. TREND_SCORE (1-10): How trending/emerging is this problem?
           - 9-10: New problem from recent tech/market shifts (AI, remote work, etc.)
           - 7-8: Growing problem with increasing mentions
           - 4-6: Established problem, steady mentions
           - 1-3: Declining or solved problem
        
        2. MARKET_SIZE: Estimate potential market
           - "large" (>$100M TAM): B2B, many industries, high frequency
           - "medium" ($10M-$100M TAM): Specific vertical or workflow
           - "small" (<$10M TAM): Very niche use case
           - "unknown": Not enough context
        
        3. COMPETITORS: List 1-3 existing solutions (or "none" if truly novel)
           - Be specific with product names if known
           - Use "generic tools" if only partial solutions exist
        
        4. DIFFICULTY (1-10): Technical complexity to build MVP
           - 1-3: Simple CRUD app, basic integrations
           - 4-6: Moderate complexity, API integrations, some AI
           - 7-10: Complex algorithms, real-time processing, heavy AI
        
        5. TIME_TO_BUILD: Estimated time for solo developer to MVP
           - "1-2 weeks": Simple automation/integration
           - "1-2 months": Standard SaaS with integrations
           - "3-6 months": Complex features or multiple integrations
           - "6+ months": Requires significant R&D or infrastructure

        GOOD EXAMPLES (Mark as pain points):
        Input: "I spend 4 hours every week manually entering Stripe payments into QuickBooks. Why isn't this automated?"
        Output: {{
            "is_pain_point": true, 
            "score": 9, 
            "solution": "StripeSync: Auto-sync Stripe transactions to QuickBooks with AI-powered category detection", 
            "reasoning": "High frequency (weekly), clear workflow pain, B2B context, measurable time cost",
            "trend_score": 6,
            "market_size": "medium",
            "competitors": "Zapier, Automate.io",
            "difficulty": 4,
            "time_to_build": "1-2 months"
        }}

        Input: "Scheduling Instagram posts for 5 clients is a nightmare. Switching between Buffer, Later, and native apps constantly."
        Output: {{
            "is_pain_point": true, 
            "score": 8, 
            "solution": "ClientPostHub: Unified dashboard to schedule posts across all clients' social accounts with bulk import", 
            "reasoning": "Multi-client workflow, integration pain, professional use case",
            "trend_score": 7,
            "market_size": "large",
            "competitors": "Hootsuite, Sprout Social",
            "difficulty": 6,
            "time_to_build": "3-6 months"
        }}

        BAD EXAMPLES (Not pain points):
        Input: "My accountant is so slow responding to emails ugh"
        Output: {{
            "is_pain_point": false, 
            "score": 2, 
            "solution": "", 
            "reasoning": "This is about service quality, not a workflow automation opportunity",
            "trend_score": 1,
            "market_size": "unknown",
            "competitors": "none",
            "difficulty": 0,
            "time_to_build": "N/A"
        }}

        Input: "Taxes are so complicated and confusing"
        Output: {{
            "is_pain_point": false, 
            "score": 3, 
            "solution": "", 
            "reasoning": "Too vague, no specific workflow mentioned, likely needs professional help not software",
            "trend_score": 2,
            "market_size": "unknown",
            "competitors": "TurboTax, H&R Block",
            "difficulty": 0,
            "time_to_build": "N/A"
        }}

        Now analyze these posts:
        {joined_posts}

        Return ONLY a JSON array of objects, one per input post, in the same order.
        Format: [{{
            "is_pain_point": bool, 
            "score": int, 
            "solution": str, 
            "reasoning": str,
            "trend_score": int,
            "market_size": str,
            "competitors": str,
            "difficulty": int,
            "time_to_build": str
        }}, ...]
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Gemini API Error: {e}")
            # Return error objects for the batch size
            return [{"error": str(e), "is_pain_point": False, "score": 0} for _ in posts]

