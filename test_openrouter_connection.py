#!/usr/bin/env python3
"""
Test script to verify OpenRouter API connection with DeepSeek R1.
Run this to ensure the integration is working before using the full app.
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

def test_openrouter_connection():
    """Test OpenRouter API with DeepSeek R1 model."""
    
    print("🔍 Testing OpenRouter API Connection...")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        print("❌ ERROR: OPENROUTER_API_KEY not found in environment")
        print("Please add it to your .env file:")
        print("OPENROUTER_API_KEY=sk-or-v1-...")
        return False
    
    print(f"✅ API Key found: {api_key[:20]}...")
    
    # Initialize OpenAI client with OpenRouter
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "https://github.com/vjwork100-hash/problem_hunter",
                "X-Title": "Problem Hunter - Test Script"
            }
        )
        print("✅ OpenAI client initialized with OpenRouter endpoint")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Test prompt - simple SaaS idea analysis
    test_prompt = """
    You are a SaaS Product Researcher analyzing posts for software business opportunities.
    
    Analyze this post and return ONLY a JSON object with the following fields:
    - is_pain_point (bool)
    - score (1-10)
    - solution (string)
    - reasoning (string)
    - trend_score (1-10)
    - market_size (string: large/medium/small/unknown)
    - competitors (string)
    - difficulty (1-10)
    - time_to_build (string)
    
    POST:
    "I hate manually syncing Stripe payments to QuickBooks every week. It takes 3 hours and I always make mistakes."
    
    Return ONLY the JSON object, no other text.
    """
    
    print("\n📤 Sending test request to DeepSeek R1...")
    print(f"Model: deepseek/deepseek-r1-0528:free")
    
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1-0528:free",
            messages=[
                {"role": "user", "content": test_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        print("✅ Response received!")
        
        # DeepSeek R1 may include <think> tags before JSON
        content = response.choices[0].message.content
        
        # Extract JSON from response (handle thinking tags)
        if "```json" in content:
            # Extract from code block
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            json_str = content[json_start:json_end].strip()
        elif "<think>" in content:
            # Extract after thinking tags
            json_start = content.find("</think>") + 8
            json_str = content[json_start:].strip()
            # Remove any remaining markdown code blocks
            if json_str.startswith("```"):
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:].strip()
        else:
            json_str = content.strip()
        
        # Parse the response
        result = json.loads(json_str)
        
        print("\n📊 Analysis Result:")
        print("=" * 60)
        print(json.dumps(result, indent=2))
        
        # Validate structure
        required_fields = [
            "is_pain_point", "score", "solution", "reasoning",
            "trend_score", "market_size", "competitors", 
            "difficulty", "time_to_build"
        ]
        
        missing_fields = [f for f in required_fields if f not in result]
        
        if missing_fields:
            print(f"\n⚠️  WARNING: Missing fields: {missing_fields}")
            return False
        
        print("\n✅ All required fields present!")
        print(f"✅ Pain Point Detected: {result['is_pain_point']}")
        print(f"✅ Viability Score: {result['score']}/10")
        print(f"✅ Solution: {result['solution'][:80]}...")
        
        print("\n" + "=" * 60)
        print("🎉 SUCCESS! OpenRouter + DeepSeek R1 integration working!")
        print("=" * 60)
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")
        print(f"Raw response: {response.choices[0].message.content}")
        return False
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

if __name__ == "__main__":
    success = test_openrouter_connection()
    exit(0 if success else 1)
