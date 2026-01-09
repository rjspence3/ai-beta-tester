# AI Beta Tester

AI-powered beta testing automation tool with browser automation.

---

## Environment Setup

```bash
# Backend: Activate virtual environment (REQUIRED before any Python commands)
source .venv/bin/activate

# Install backend dependencies
pip install -e .

# Frontend: Install dependencies
cd ui && npm install
```

---

## Local Access

| Service | Domain | Port |
|---------|--------|------|
| Frontend (Next.js) | http://ai-beta-tester.test | 3080 |
| Backend API | http://ai-beta-tester-api.test | 8765 |

Port assignments are defined in `~/Development/dev/ports.json` (authoritative).

---

## Commands

```bash
# Start backend API
ai-beta-test ui --no-browser

# Start frontend
cd ui && npm run dev

# Run tests
pytest
```

---

## Notes

- Uses Playwright for browser automation
- Next.js frontend + FastAPI backend

---

## Structure

```
ai-beta-reports/
  beta_test_fuzz-2142-low_20251229_095509/
    screenshots/
    sessions/
  beta_test_fuzz-29541-medium_20251229_095621/
    screenshots/
    sessions/
  beta_test_fuzz-29613-low_20251229_100044/
    screenshots/
    sessions/
  beta_test_fuzz-9085-medium_20251229_095506/
    screenshots/
    sessions/
  beta_test_fuzz-9556-medium_20251229_100315/
    screenshots/
    sessions/
docs/
reports/
  appflow/
    screenshots/
    sessions/
  expert-council/
    done/
  napgpt/
    screenshots/
    sessions/
  napgpt_run_01/
    screenshots/
    sessions/
  napgpt_run_1/
    screenshots/
    sessions/
  napgpt_run_2/
    screenshots/
    sessions/
  napgpt_run_3/
    screenshots/
    sessions/
  napgpt_run_4/
    screenshots/
    sessions/
  napgpt_run_5/
    screenshots/
    sessions/
  napgpt_run_exploit/
    screenshots/
    sessions/
screenshots/
sessions/
src/
  ai_beta_tester/
    api/
    experiments/
    models/
    personalities/
    reporting/
    scoring/
    suites/
    tools/
  ai_beta_tester.egg-info/
tests/
  contract/
  integration/
  suites/
    fixtures/
  unit/
ui/
  src/
    app/
    components/
    hooks/
    lib/
```
