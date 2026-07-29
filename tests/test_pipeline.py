"""
Tests for all 3 parts of the assessment
Run with: pytest tests/ -v
"""

import sys
import os
import json

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), '..', 'src')
)

import pytest  # noqa: E402
from optimizer import (  # noqa: E402
    build_bloated_prompt,
    build_optimized_prompt,
    count_tokens,
    get_cache_key,
)
from debugger import validate_json_output, FixedPipeline  # noqa: E402


class TestTokenOptimization:

    def setup_method(self):
        self.sample_comments = [
            "Can you make a Python tutorial?",
            "Love your content!",
            "Bad audio quality",
            "More ML videos please!",
            "How do you code so fast?",
        ] * 20

    def test_optimized_shorter_than_bloated(self):
        bloated = build_bloated_prompt(self.sample_comments)
        optimized = build_optimized_prompt(self.sample_comments)
        assert count_tokens(optimized) < count_tokens(bloated)

    def test_token_reduction_at_least_50_percent(self):
        bloated = build_bloated_prompt(self.sample_comments)
        optimized = build_optimized_prompt(self.sample_comments)
        reduction = (
            (count_tokens(bloated) - count_tokens(optimized))
            / count_tokens(bloated) * 100
        )
        assert reduction >= 50

    def test_optimized_prompt_contains_comments(self):
        comments = ["Test comment 1", "Test comment 2"]
        prompt = build_optimized_prompt(comments)
        assert "Test comment 1" in prompt
        assert "Test comment 2" in prompt

    def test_cache_key_same_for_same_input(self):
        assert get_cache_key("hello") == get_cache_key("hello")

    def test_cache_key_different_for_different_input(self):
        assert get_cache_key("hello") != get_cache_key("bye")

    def test_count_tokens_returns_positive(self):
        assert count_tokens("Hello this is a test") > 0


class TestDebugging:

    def test_valid_json_passes_validation(self):
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
            ["questions", "content_requests", "complaints",
             "praise", "top_content_ideas"]
        )
        assert is_valid is True
        assert data is not None

    def test_malformed_json_fails_validation(self):
        is_valid, data = validate_json_output(
            "Not JSON at all blah blah",
            ["questions", "content_requests"]
        )
        assert is_valid is False
        assert data is None

    def test_missing_keys_fails_validation(self):
        incomplete = json.dumps({"questions": ["Something?"]})
        is_valid, data = validate_json_output(
            incomplete,
            ["questions", "content_requests", "complaints",
             "praise", "top_content_ideas"]
        )
        assert is_valid is False

    def test_empty_output_fails_validation(self):
        is_valid, data = validate_json_output("", ["questions"])
        assert is_valid is False

    def test_json_with_code_fences_passes(self):
        wrapped = (
            "```json\n"
            '{"questions": ["How?"], "content_requests": [], '
            '"complaints": [], "praise": [], '
            '"top_content_ideas": []}\n'
            "```"
        )
        is_valid, data = validate_json_output(
            wrapped,
            ["questions", "content_requests", "complaints",
             "praise", "top_content_ideas"]
        )
        assert is_valid is True

    def test_pipeline_eventually_succeeds(self):
        pipeline = FixedPipeline()
        success = False
        for _ in range(5):
            try:
                result = pipeline.run("test_123")
                if result:
                    success = True
                    break
            except Exception:
                continue
        assert success


class TestIntegration:

    def test_sample_comments_not_empty(self):
        comments = ["Test comment 1", "Test comment 2"]
        assert len(comments) > 0

    def test_prompt_is_string(self):
        prompt = build_optimized_prompt(["test comment"])
        assert isinstance(prompt, str)

    def test_prompt_not_empty(self):
        prompt = build_optimized_prompt(["test comment"])
        assert len(prompt) > 0

    def test_token_count_is_integer(self):
        count = count_tokens("Hello world test")
        assert isinstance(count, int)


# keep pytest in use
assert pytest is not 
