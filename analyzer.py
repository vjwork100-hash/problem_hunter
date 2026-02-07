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
        You are a SaaS Product Researcher analyzing Reddit posts for software business opportunities.

        CRITICAL RULES:
        - Only mark as pain point if it's a REPEATABLE WORKFLOW problem (not one-off complaints)
        - Must be solvable by software (not human service/physical work)
        - Must indicate willingness to pay (time-consuming, business context, frequency mentioned)

        SCORING GUIDE (1-10):
        - 9-10: Repeated frequently ("every week"), clear workflow, B2B context, high frustration
        - 7-8: Clear automation opportunity, some frequency indicators, measurable pain
        - 4-6: Valid problem but niche/unclear market size
        - 1-3: Vague complaint, one-off issue, or already solved by existing tools

        GOOD EXAMPLES (Mark as pain points):
        Input: "I spend 4 hours every week manually entering Stripe payments into QuickBooks. Why isn't this automated?"
        Output: {{"is_pain_point": true, "score": 9, "solution": "StripeSync: Auto-sync Stripe transactions to QuickBooks with AI-powered category detection", "reasoning": "High frequency (weekly), clear workflow pain, B2B context, measurable time cost"}}

        Input: "Scheduling Instagram posts for 5 clients is a nightmare. Switching between Buffer, Later, and native apps constantly."
        Output: {{"is_pain_point": true, "score": 8, "solution": "ClientPostHub: Unified dashboard to schedule posts across all clients' social accounts with bulk import", "reasoning": "Multi-client workflow, integration pain, professional use case"}}

        BAD EXAMPLES (Not pain points):
        Input: "My accountant is so slow responding to emails ugh"
        Output: {{"is_pain_point": false, "score": 2, "solution": "", "reasoning": "This is about service quality, not a workflow automation opportunity"}}

        Input: "Taxes are so complicated and confusing"
        Output: {{"is_pain_point": false, "score": 3, "solution": "", "reasoning": "Too vague, no specific workflow mentioned, likely needs professional help not software"}}

        Input: "Just got scammed by a freelancer on Fiverr, be careful everyone"
        Output: {{"is_pain_point": false, "score": 1, "solution": "", "reasoning": "One-off incident, seeking support not expressing workflow pain"}}

        Now analyze these posts:
        {joined_posts}

        Return ONLY a JSON array of objects, one per input post, in the same order.
        Format: [{{"is_pain_point": bool, "score": int, "solution": str, "reasoning": str}}, ...]
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

