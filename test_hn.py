#!/usr/bin/env python3
"""Quick test script for Hacker News source."""

from sources.hackernews_source import HackerNewsSource

def test_hn():
    print("Testing Hacker News Source...")
    print("-" * 50)
    
    hn = HackerNewsSource()
    keywords = ["frustrated", "manual", "tedious"]
    
    print(f"Fetching posts with keywords: {keywords}")
    posts = hn.fetch_posts(keywords, limit=5)
    
    print(f"\nFound {len(posts)} posts:\n")
    
    for i, post in enumerate(posts, 1):
        print(f"{i}. [{post['score']} pts] {post['title']}")
        print(f"   Source: {post['source']} | Comments: {post['num_comments']}")
        print(f"   URL: {post['url']}")
        print()

if __name__ == "__main__":
    test_hn()
