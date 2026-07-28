# AI Pipeline Assessment
### Audience Comment Miner — Token Optimization + Debugging + CI/CD

---

## 🚀 Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/ai-pipeline-assessment
cd ai-pipeline-assessment

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Edit .env and add your API keys

# 4. Run the pipeline
python src/pipeline.py

# 5. Run tests
pytest tests/ -v
```

---

## Part 1 — Token/Cost Optimization

### Problem
Agent pipeline burning ~100K input tokens per query.
Expensive and slow at scale.

### Solution: 2 Optimizations

**Optimization 1: Prompt Compression**
- Removed bloated system instructions (repeated 20x)
- Kept only last 50 comments instead of all 1000+
- Removed redundant examples
- Switched to structured JSON output format
- Result: JSON output is faster to parse too

**Optimization 2: Caching Layer**
- MD5 hash of prompt used as cache key
- Same comments = 0 API tokens used
- In-memory cache (can be upgraded to Redis)

### Before/After Token Counts

| Component | Before | After | Saved |
|---|---|---|---|
| System prompt | 2,000 | 200 | 90% |
| Comment history | 80,000 | 5,000 | 94% |
| Examples | 17,500 | 1,500 | 91% |
| User message | 500 | 500 | 0% |
| **TOTAL** | **~100,000** | **~7,200** | **93%** |

### Quality Tradeoffs
- Prompt compression: Minimal — kept most relevant context
- Caching: None — exact same output every time

---

## Part 2 — Debugging

### The Problem
Multi-step pipeline with 3 failure modes:
1. Intermittent timeouts
2. Malformed JSON output
3. Silent wrong data (missing keys)

### Debugging Process

**Step 1: Added structured logging**
- Every step logged with timestamp + duration
- DEBUG level shows raw AI output
- Saved to `pipeline.log` file

**Step 2: Identified failure modes**
- Timeout → YouTube API slow response
- Malformed → AI returns text instead of JSON
- Silent wrong → AI returns JSON missing required keys

**Step 3: Added retry decorator**
- 3 attempts with exponential backoff
- Handles: timeouts, API errors, validation failures

**Step 4: Added output validator**
- Checks JSON is valid
- Strips ``` code fences AI adds
- Checks all required keys exist
- Logs exactly what is wrong

### Tools Used
- Python `logging` module → structured logs
- `@retry` decorator → handles intermittent failures
- `validate_json_output()` → catches malformed/missing data
- `pipeline.log` → full audit trail

---

## Part 3 — CI/CD Pipeline

### GitHub Actions Workflow

**On every push:**
- Runs flake8 linting
- Runs pytest test suite
- Reports coverage

**On merge to main:**
- Deploys to Render staging automatically
- Health check after deployment
- Notifies on success/failure

### Secrets Management

**Never hardcode API keys!**

```bash
# In GitHub repo:
Settings → Secrets and Variables → Actions
→ Add: GEMINI_API_KEY
→ Add: YOUTUBE_API_KEY
→ Add: RENDER_API_KEY
→ Add: RENDER_SERVICE_ID
```

In workflow file, reference as:
```yaml
env:
  GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
```

### Rollback Plan

**First 5 minutes if production breaks:**

```
Minute 1 → Detect: Check Render dashboard + logs
Minute 2 → Revert: Render → Deploys → Rollback button
            (One click — restores previous version)
Minute 3 → Verify: Test live URL + check logs clean
Minute 4 → Notify: Team message "Reverted — investigating"
Minute 5 → Investigate: git log to find breaking commit
```

**Prevention:**
- Staging environment catches issues before production
- Health check in CI/CD catches broken deploys
- Tests must pass before any deploy happens

---

## Project Structure

```
ai-pipeline-assessment/
├── .github/
│   └── workflows/
│       └── pipeline.yml    ← CI/CD (Part 3)
├── src/
│   ├── optimizer.py        ← Token optimization (Part 1)
│   ├── debugger.py         ← Debugging fixes (Part 2)
│   └── pipeline.py         ← Main combined pipeline
├── tests/
│   └── test_pipeline.py    ← All tests
├── .env.example            ← Environment template
├── .gitignore              ← Never commit .env!
├── requirements.txt
└── README.md
```

---

## Tech Stack
- Python 3.11
- Google Gemini 2.0 Flash API
- YouTube Data API v3
- GitHub Actions (CI/CD)
- Render (Deployment)
- pytest (Testing)
- flake8 (Linting)
