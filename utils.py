"""
Utility functions for pain point detection and filtering.
Provides centralized keyword management, pain scoring, and spam filtering.
"""

import re
from typing import Dict, List, Any

# 6 Categories of Pain Keywords (60+ total)
PAIN_KEYWORDS = {
    "pain": [
        "hate", "frustrated", "annoying", "tedious", "painful", "nightmare",
        "terrible", "awful", "sucks", "irritating", "exhausting", "draining"
    ],
    "time": [
        "hours", "waste", "slow", "taking forever", "time-consuming", 
        "forever", "daily", "weekly", "every day", "every week", "constantly"
    ],
    "seeking": [
        "looking for", "need", "want", "wish", "alternative to", "better than",
        "replacement for", "instead of", "searching for", "trying to find"
    ],
    "problems": [
        "can't", "unable", "doesn't work", "broken", "missing", "lack of",
        "no way to", "impossible", "failing", "error", "bug", "issue"
    ],
    "business": [
        "losing money", "costing", "revenue", "customers leaving", "churn",
        "expensive", "paying too much", "budget", "ROI", "profit"
    ],
    "workflow": [
        "manual", "repetitive", "copy-paste", "switching between", "juggling",
        "back and forth", "multiple tools", "scattered", "disorganized"
    ]
}

# Keyword weights for pain scoring
KEYWORD_WEIGHTS = {
    "pain": 20,
    "time": 15,
    "seeking": 10,
    "problems": 10,
    "business": 25,
    "workflow": 15
}


def get_expanded_pain_keywords() -> List[str]:
    """
    Returns all pain keywords as a flat list.
    Use this to replace local pain_keywords in source files.
    """
    all_keywords = []
    for category_keywords in PAIN_KEYWORDS.values():
        all_keywords.extend(category_keywords)
    return all_keywords


def get_pain_score(text: str) -> int:
    """
    Calculate pain intensity score (0-100) based on keyword matches.
    
    Scoring logic:
    - Pain keywords: +20 each
    - Time indicators: +15 each
    - Seeking solutions: +10 each
    - Problems: +10 each
    - Business impact: +25 each
    - Workflow gaps: +15 each
    - Frequency words (daily, weekly): +10
    - Numbers (10 hours, $500): +5 each
    
    Args:
        text: Combined title + body text
        
    Returns:
        Score from 0-100
    """
    if not text:
        return 0
    
    text_lower = text.lower()
    score = 0
    
    # Check each category
    for category, keywords in PAIN_KEYWORDS.items():
        weight = KEYWORD_WEIGHTS[category]
        for keyword in keywords:
            if keyword in text_lower:
                score += weight
                break  # Only count once per category
    
    # Bonus for frequency indicators
    frequency_words = ["daily", "weekly", "every day", "every week", "constantly", "always"]
    if any(word in text_lower for word in frequency_words):
        score += 10
    
    # Bonus for numbers (indicates measurable pain)
    # Match patterns like "10 hours", "$500", "3 times"
    number_patterns = [
        r'\d+\s*(hours?|minutes?|days?|weeks?|months?)',
        r'\$\d+',
        r'\d+\s*times?',
        r'\d+%'
    ]
    for pattern in number_patterns:
        if re.search(pattern, text_lower):
            score += 5
            break
    
    # Cap at 100
    return min(score, 100)


def is_likely_spam(text: str) -> bool:
    """
    Less aggressive spam filter - only catches obvious spam.
    
    Filters:
    - All caps + excessive punctuation
    - Promotional language
    - Very short text (<10 chars)
    
    Args:
        text: Combined title + body text
        
    Returns:
        True if likely spam, False otherwise
    """
    if not text or len(text.strip()) < 10:
        return True
    
    # Check for all caps + excessive punctuation
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    exclamation_count = text.count('!')
    if caps_ratio > 0.7 and exclamation_count > 3:
        return True
    
    # Check for promotional language
    spam_phrases = [
        "buy now", "limited offer", "click here", "subscribe now",
        "free trial", "sign up today", "limited time", "act now",
        "special offer", "discount code", "promo code"
    ]
    text_lower = text.lower()
    spam_count = sum(1 for phrase in spam_phrases if phrase in text_lower)
    if spam_count >= 2:
        return True
    
    return False


def prefilter_post(post: Dict[str, Any], min_pain_score: int = 5) -> bool:
    """
    Quick filter to determine if a post is worth AI analysis.
    
    Args:
        post: Post dict with 'title' and 'text' fields
        min_pain_score: Minimum pain score to pass (default 5)
        
    Returns:
        True if post should be analyzed, False to skip
    """
    # Combine title and text
    text = f"{post.get('title', '')} {post.get('text', '')}"
    
    # Filter spam first
    if is_likely_spam(text):
        return False
    
    # Check pain score
    pain_score = get_pain_score(text)
    return pain_score >= min_pain_score


def format_timestamp(unix_timestamp: int) -> str:
    """
    Convert Unix timestamp to readable date string.
    
    Args:
        unix_timestamp: Unix timestamp (seconds since epoch)
        
    Returns:
        Formatted date string (YYYY-MM-DD)
    """
    from datetime import datetime
    try:
        dt = datetime.fromtimestamp(unix_timestamp)
        return dt.strftime('%Y-%m-%d')
    except (ValueError, OSError):
        return "Unknown"


def get_category_breakdown(text: str) -> Dict[str, bool]:
    """
    Get which pain categories are present in the text.
    Useful for debugging and understanding why a post scored high/low.
    
    Args:
        text: Combined title + body text
        
    Returns:
        Dict mapping category names to presence (True/False)
    """
    if not text:
        return {cat: False for cat in PAIN_KEYWORDS.keys()}
    
    text_lower = text.lower()
    breakdown = {}
    
    for category, keywords in PAIN_KEYWORDS.items():
        breakdown[category] = any(keyword in text_lower for keyword in keywords)
    
    return breakdown
