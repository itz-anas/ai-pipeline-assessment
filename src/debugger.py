"""
Part 2 — Debugging Broken Pipeline
Handles: timeouts, malformed output, silent wrong data
"""

import logging
import time
import json
import random
from functools import wraps
from typing import Callable

# ── LOGGING SETUP ────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pipeline.log")
    ]
)
logger = logging.getLogger("pipeline")


# ════════════════════════════════════════════════════════
# DECORATORS
# ════════════════════════════════════════════════════════

def retry(max_attempts: int = 3, delay: float = 2.0):
    """Retry decorator for intermittent failures"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.info(
                        f"Attempt {attempt}/{max_attempts}: "
                        f"{func.__name__}"
                    )
                    return func(*args, **kwargs)
                except TimeoutError as e:
                    logger.warning(
                        f"TIMEOUT on attempt {attempt}: {e}"
                    )
                    if attempt == max_attempts:
                        logger.error(
                            f"All {max_attempts} attempts failed "
                            f"for {func.__name__}"
                        )
                        raise
                    time.sleep(delay * attempt)
                except Exception as e:
                    logger.error(
                        f"Error on attempt {attempt}: {e}"
                    )
                    if attempt == max_attempts:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator


def timed(func: Callable):
    """Track execution time of each step"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        logger.info(f"START: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start
            logger.info(
                f"SUCCESS: {func.__name__} "
                f"({duration:.2f}s)"
            )
            return result
        except Exception as e:
            duration = time.time() - start
            logger.error(
                f"FAILED: {func.__name__} "
                f"({duration:.2f}s) — {e}"
            )
            raise
    return wrapper


# ════════════════════════════════════════════════════════
# OUTPUT VALIDATOR
# ════════════════════════════════════════════════════════

def validate_json_output(
    output: str,
    required_keys: list
) -> tuple:
    """
    Catches malformed output and missing keys
    the silent wrong data bug killer
    """
    if not output or not output.strip():
        logger.error("VALIDATION FAILED: Empty output!")
        return False, None

    try:
        cleaned = output.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        data = json.loads(cleaned.strip())
        logger.debug("JSON parsed successfully")

    except json.JSONDecodeError as e:
        logger.error(f"MALFORMED JSON: {e}")
        logger.debug(f"Raw output was: {output[:200]}")
        return False, None

    missing = [k for k in required_keys if k not in data]
    if missing:
        logger.error(f"MISSING REQUIRED KEYS: {missing}")
        logger.debug(f"Got keys: {list(data.keys())}")
        return False, None

    empty_keys = [
        k for k in required_keys
        if not data.get(k) and data.get(k) != 0
    ]
    if empty_keys:
        logger.warning(f"EMPTY VALUES for keys: {empty_keys}")

    logger.info("Output validation PASSED")
    return True, data


# ════════════════════════════════════════════════════════
# SIMULATED BROKEN PIPELINE (for demo)
# ════════════════════════════════════════════════════════

class BrokenPipeline:
    """Simulates the intermittent failures described"""

    def __init__(self):
        self.call_count = 0

    def fetch_comments(self, video_id: str) -> list:
        """Simulates intermittent timeout"""
        self.call_count += 1

        if random.random() < 0.3:
            raise TimeoutError(
                f"YouTube API timed out after 30s "
                f"for video {video_id}"
            )

        return [
            "Can you make a Python tutorial?",
            "Love your content!",
            "The audio was bad",
            "Please cover machine learning!",
        ]

    def analyze_with_ai(self, comments: list) -> str:
        """Simulates malformed JSON output"""

        if random.random() < 0.2:
            return "Here are the results: blah blah"

        if random.random() < 0.2:
            return json.dumps({
                "questions": ["How do you code?"],
            })

        return json.dumps({
            "questions": ["How do you code?"],
            "content_requests": [
                {"idea": "Python tutorial", "count": 3}
            ],
            "complaints": ["Bad audio"],
            "praise": ["Love your content!"],
            "top_content_ideas": [
                {
                    "rank": 1,
                    "idea": "Python tutorial",
                    "reason": "Most requested"
                }
            ]
        })


# ════════════════════════════════════════════════════════
# FIXED PIPELINE WITH DEBUGGING
# ════════════════════════════════════════════════════════

class FixedPipeline:
    """The debugged, production-ready pipeline"""

    def __init__(self):
        self.broken = BrokenPipeline()
        self.required_keys = [
            "questions",
            "content_requests",
            "complaints",
            "praise",
            "top_content_ideas"
        ]

    @timed
    @retry(max_attempts=3, delay=1.0)
    def fetch_comments(self, video_id: str) -> list:
        """Step 1: Fetch with retry on timeout"""
        logger.info(f"Fetching comments for: {video_id}")
        comments = self.broken.fetch_comments(video_id)
        logger.info(f"Fetched {len(comments)} comments")
        return comments

    @timed
    @retry(max_attempts=3, delay=1.0)
    def analyze_comments(self, comments: list) -> dict:
        """Step 2: Analyze with validation"""
        logger.info(f"Analyzing {len(comments)} comments...")

        raw_output = self.broken.analyze_with_ai(comments)
        logger.debug(f"Raw AI output: {raw_output[:100]}")

        is_valid, data = validate_json_output(
            raw_output,
            self.required_keys
        )

        if not is_valid:
            raise ValueError(
                "AI output failed validation — retrying..."
            )

        return data

    @timed
    def format_report(self, analysis: dict) -> str:
        """Step 3: Format final report"""
        ideas = analysis.get("top_content_ideas", [])
        questions = analysis.get("questions", [])
        requests = analysis.get("content_requests", [])

        report = "WEEKLY AUDIENCE INSIGHTS REPORT\n"
        report += "=" * 40 + "\n\n"

        report += "TOP CONTENT IDEAS:\n"
        for idea in ideas:
            report += (
                f"  #{idea.get('rank')}: "
                f"{idea.get('idea')} — "
                f"{idea.get('reason')}\n"
            )

        report += f"\nQUESTIONS ({len(questions)}):\n"
        for q in questions:
            report += f"  - {q}\n"

        report += f"\nCONTENT REQUESTS ({len(requests)}):\n"
        for r in requests:
            report += (
                f"  - {r.get('idea')} "
                f"(requested {r.get('count', 1)}x)\n"
            )

        return report

    def run(self, video_id: str = "dQw4w9WgXcQ") -> str:
        """Run the complete fixed pipeline"""
        logger.info("STARTING FIXED PIPELINE")

        try:
            comments = self.fetch_comments(video_id)
            analysis = self.analyze_comments(comments)
            report = self.format_report(analysis)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            return report

        except Exception as e:
            logger.error(f"PIPELINE FAILED: {e}")
            raise


# ════════════════════════════════════════════════════════
# DEBUG DEMO
# ════════════════════════════════════════════════════════

def run_debugging_demo():
    print("\n" + "=" * 60)
    print("PART 2: DEBUGGING DEMO")
    print("=" * 60)

    pipeline = FixedPipeline()

    for run in range(1, 4):
        print(f"\n--- Run {run} ---")
        try:
            report = pipeline.run("test_video_123")
            print("\n" + report)
            break
        except Exception as e:
            print(f"Run {run} ultimately failed: {e}")
            if run < 3:
                print("Trying again...")


if __name__ == "__main__":
    run_debugging_demo()