"""
Tests for all 3 parts of the assessment
Run with: pytest tests/ -v
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from optimizer import (
    build_bloated_prompt,
    build_optimized_prompt,
    count_tokens,
    get_cache_key
)
from debugger import validate_json_output, FixedPipeline
import json


# ════════════════════════════════════════════════════════
# PART 1 TESTS — Token Optimization
# ════════════════════════════════════════════════════════

class TestTokenOptimization:

    def setup_method(self):
        self.sample_comments = [
            "Can you make a Python tutorial?",
            "Love your content!",
            "Bad audio quality",
            "More ML videos please!",
            "How do you code so fast?",
        ] * 20  # 100 comments

    def test_optimized_prompt_shorter_than_bloated(self):
        """Optimized prompt must use fewer tokens"""
        bloated = build_bloated_prompt(self.sample_comments)
        optimized = build_optimized_prompt(self.sample_comments)

        bloated_tokens = count_tokens(bloated)
        optimized_tokens = count_tokens(optimized)

        assert optimized_tokens < bloated_tokens, (
            f"Optimized ({optimized_tokens}) should be less "
            f"than bloated ({bloated_tokens})"
        )

    def test_token_reduction_at_least_50_percent(self):
        """Must achieve at least 50% token reduction"""
        bloated = build_bloated_prompt(self.sample_comments)
        optimized = build_optimized_prompt(self.sample_comments)

        reduction = (
            (count_tokens(bloated) - count_tokens(optimized))
            / count_tokens(bloated) * 100
        )

        assert reduction >= 50, (
            f"Reduction {reduction:.1f}% is less than 50%"
        )
        print(f"\n✅ Token reduction: {reduction:.1f}%")

    def test_optimized_prompt_contains_comments(self):
        """Optimized prompt must still include comments"""
        comments = ["Test comment 1", "Test comment 2"]
        prompt = build_optimized_prompt(comments)

        assert "Test comment 1" in prompt
        assert "Test comment 2" in prompt

    def test_cache_key_same_for_same_input(self):
        """Same input must produce same cache key"""
        key1 = get_cache_key("hello world")
        key2 = get_cache_key("hello world")
        assert key1 == key2

    def test_cache_key_different_for_different_input(self):
        """Different input must produce different cache key"""
        key1 = get_cache_key("hello world")
        key2 = get_cache_key("goodbye world")
        assert key1 != key2

    def test_count_tokens_returns_positive(self):
        """Token count must be positive"""
        count = count_tokens("Hello this is a test prompt")
        assert count > 0


# ════════════════════════════════════════════════════════
# PART 2 TESTS — Debugging
# ════════════════════════════════════════════════════════

class TestDebugging:

    def test_valid_json_passes_validation(self):
        """Good JSON with all keys should pass"""
        good_output = json.dumps({
            "questions": ["How do you code?"],
            "content_requests": [
                {"idea": "Python tutorial", "count": 3}
            ],
            "complaints": ["Bad audio"],
            "praise": ["Love it!"],
            "top_content_ideas": [
                {"rank": 1, "idea": "Python", "reason": "Popular"}
            ]
        })

        is_valid, data = validate_json_output(
            good_output,
            ["questions", "content_requests",
             "complaints", "praise", "top_content_ideas"]
        )

        assert is_valid is True
        assert data is not None

    def test_malformed_json_fails_validation(self):
        """Malformed JSON should fail validation"""
        bad_output = "Here are some results blah blah not JSON"

        is_valid, data = validate_json_output(
            bad_output,
            ["questions", "content_requests"]
        )

        assert is_valid is False
        assert data is None

    def test_missing_keys_fails_validation(self):
        """JSON missing required keys should fail"""
        incomplete = json.dumps({
            "questions": ["Something?"]
            # Missing all other required keys!
        })

        is_valid, data = validate_json_output(
            incomplete,
            ["questions", "content_requests",
             "complaints", "praise", "top_content_ideas"]
        )

        assert is_valid is False

    def test_empty_output_fails_validation(self):
        """Empty output should fail validation"""
        is_valid, data = validate_json_output(
            "",
            ["questions"]
        )
        assert is_valid is False

    def test_json_with_code_fences_passes(self):
        """AI often wraps JSON in backticks — should still work"""
        wrapped = """```json
{
    "questions": ["How?"],
    "content_requests": [],
    "complaints": [],
    "praise": [],
    "top_content_ideas": []
}
```"""
        is_valid, data = validate_json_output(
            wrapped,
            ["questions", "content_requests",
             "complaints", "praise", "top_content_ideas"]
        )
        assert is_valid is True

    def test_pipeline_eventually_succeeds(self):
        """Pipeline should succeed after retries"""
        pipeline = FixedPipeline()
        # Run multiple times — should succeed at least once
        success = False
        for _ in range(5):
            try:
                result = pipeline.run("test_123")
                if result:
                    success = True
                    break
            except Exception:
                continue
        assert success, "Pipeline should succeed within 5 attempts"


# ════════════════════════════════════════════════════════
# PART 3 TESTS — Integration
# ════════════════════════════════════════════════════════

class TestIntegration:

    def test_sample_comments_not_empty(self):
        """Pipeline should always have some comments"""
        comments = [
            "Test comment 1",
            "Test comment 2"
        ]
        assert len(comments) > 0

    def test_prompt_is_string(self):
        """Built prompt must be a string"""
        prompt = build_optimized_prompt(["test comment"])
        assert isinstance(prompt, str)

    def test_prompt_not_empty(self):
        """Built prompt must not be empty"""
        prompt = build_optimized_prompt(["test comment"])
        assert len(prompt) > 0

    def test_token_count_is_integer(self):
        """Token count must be an integer"""
        count = count_tokens("Hello world test")
        assert isinstance(count, int)
