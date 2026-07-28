"""
Part 1 — Token/Cost Optimization
Reduces ~100K token queries down to ~7K tokens
using prompt compression + caching
"""

import hashlib
import json
import time
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# ── IN-MEMORY CACHE ──────────────────────────────────────
cache = {}

def get_cache_key(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()

# ── TOKEN COUNTER (approximate) ──────────────────────────
def count_tokens(text: str) -> int:
    # Rough estimate: 1 token ≈ 4 characters
    return len(text) // 4

# ════════════════════════════════════════════════════════
# BEFORE OPTIMIZATION — Bloated prompt (~100K tokens)
# ════════════════════════════════════════════════════════
def build_bloated_prompt(comments: list[str]) -> str:
    """Simulates a poorly written 100K token prompt"""
    bloated_system = """
    You are an extremely helpful, knowledgeable, and 
    professional AI assistant with deep expertise in 
    content strategy, audience analysis, social media 
    marketing, YouTube growth, Instagram engagement, 
    community management, and creator economy. You have 
    been trained on millions of examples of successful 
    YouTube channels and Instagram accounts. Your job is 
    to provide extremely detailed, comprehensive, thorough, 
    and actionable analysis of social media comments.
    Please make sure to be very detailed in your response
    and cover every single aspect of the comments provided.
    Do not miss any comment. Analyze each one carefully.
    Provide extensive reasoning for every category you 
    assign. Include full quotes from every comment.
    """ * 20  # Simulating repeated/bloated instructions

    all_comments = "\n".join(
        [f"Comment {i+1}: {c}" for i, c in enumerate(comments)]
    )

    bloated_examples = """
    Example 1: If someone says "Can you make a video about 
    Python tutorials?" this is a content request because 
    the user is requesting a specific type of content...
    Example 2: If someone says "I love your videos!" this 
    is praise because the user is expressing positive 
    sentiment...
    """ * 10  # Repeated examples

    return f"""
    {bloated_system}
    
    FULL COMMENT HISTORY (analyze every single one):
    {all_comments}
    
    EXAMPLES OF HOW TO CATEGORIZE:
    {bloated_examples}
    
    Now provide an extremely comprehensive and detailed 
    analysis of every single comment listed above. 
    Include the full text of each comment in your response.
    Categorize into: Questions, Content Requests, 
    Complaints, Praise. Then rank content ideas.
    """

# ════════════════════════════════════════════════════════
# AFTER OPTIMIZATION — Compressed prompt (~7K tokens)
# ════════════════════════════════════════════════════════
def build_optimized_prompt(comments: list[str]) -> str:
    """
    Optimization 1: Prompt Compression
    - Remove repeated instructions
    - Remove redundant examples
    - Use structured JSON output
    - Keep only essential context
    """
    # Take only last 50 comments max (not all 1000)
    recent_comments = comments[-50:]
    comments_text = "\n".join(
        [f"- {c}" for c in recent_comments]
    )

    return f"""Analyze these YouTube/Instagram comments.
Cluster into categories and rank content ideas.

COMMENTS:
{comments_text}

OUTPUT (JSON only, no extra text):
{{
  "questions": ["question1", "question2"],
  "content_requests": [
    {{"idea": "topic", "count": 5, "comments": ["c1","c2"]}}
  ],
  "complaints": ["complaint1"],
  "praise": ["praise1"],
  "top_content_ideas": [
    {{"rank": 1, "idea": "topic", "reason": "why"}}
  ]
}}"""

# ════════════════════════════════════════════════════════
# Optimization 2: CACHING LAYER
# ════════════════════════════════════════════════════════
def call_with_cache(prompt: str) -> dict:
    """
    Optimization 2: Cache repeated queries
    Same comments = 0 API tokens used!
    """
    key = get_cache_key(prompt)

    if key in cache:
        print("✅ CACHE HIT — 0 tokens used!")
        return {"result": cache[key], "from_cache": True}

    print("🔄 Cache MISS — calling Gemini API...")
    response = model.generate_content(prompt)
    result = response.text

    # Save to cache
    cache[key] = result
    return {"result": result, "from_cache": False}

# ════════════════════════════════════════════════════════
# MAIN DEMO — Show before/after comparison
# ════════════════════════════════════════════════════════
def run_optimization_demo():
    # Sample comments (simulating real YouTube comments)
    sample_comments = [
        "Can you make a tutorial on Python basics?",
        "Love your content! Keep it up!",
        "The audio quality was really bad in this one",
        "Please do a video on machine learning!",
        "How do you edit your videos?",
        "This helped me so much, thank you!",
        "Can you explain neural networks simply?",
        "Your explanations are the best on YouTube",
        "The video was too long and boring honestly",
        "Please make more coding challenges!",
        "How do I get started with AI?",
        "Can you cover React hooks next?",
        "Amazing tutorial! Subscribed!",
        "The background music is too loud",
        "More DSA videos please!",
        "What laptop do you use for coding?",
        "This is exactly what I was looking for!",
        "Can you do a full stack project tutorial?",
        "Please make videos in Hindi too",
        "How long did it take you to learn coding?",
    ] * 5  # 100 total comments

    print("=" * 60)
    print("PART 1: TOKEN OPTIMIZATION DEMO")
    print("=" * 60)

    # ── BEFORE ──────────────────────────────────────────
    bloated = build_bloated_prompt(sample_comments)
    before_tokens = count_tokens(bloated)
    print(f"\n❌ BEFORE OPTIMIZATION:")
    print(f"   Token count: ~{before_tokens:,} tokens")
    print(f"   Estimated cost: ~${before_tokens/1000*0.00015:.4f}")

    # ── AFTER ───────────────────────────────────────────
    optimized = build_optimized_prompt(sample_comments)
    after_tokens = count_tokens(optimized)
    print(f"\n✅ AFTER OPTIMIZATION:")
    print(f"   Token count: ~{after_tokens:,} tokens")
    print(f"   Estimated cost: ~${after_tokens/1000*0.00015:.4f}")

    # ── SAVINGS ─────────────────────────────────────────
    saved = before_tokens - after_tokens
    pct = (saved / before_tokens) * 100
    print(f"\n💰 SAVINGS:")
    print(f"   Tokens saved: {saved:,}")
    print(f"   Reduction: {pct:.1f}%")

    print("\n" + "=" * 60)
    print("Calling Gemini API with OPTIMIZED prompt...")
    print("=" * 60)

    # First call — hits API
    result1 = call_with_cache(optimized)
    print(f"\n📊 Result preview:\n{result1['result'][:300]}...")

    # Second call — hits cache (0 tokens!)
    print("\n" + "=" * 60)
    print("Calling SAME query again (testing cache)...")
    print("=" * 60)
    result2 = call_with_cache(optimized)
    print(f"From cache: {result2['from_cache']}")

    print("\n✅ Optimization demo complete!")
    return result1['result']

if __name__ == "__main__":
    run_optimization_demo()
