<!-- AUTO-GENERATED from ports.json — do not edit manually -->
<!-- Regenerate: python3 ~/Development/generate_claude_md.py --apply -->

# Ai Beta Tester

FastAPI + JavaScript + Python project.

---

## Environment Setup

```bash
# Activate virtual environment (REQUIRED)
source .venv/bin/activate

# Install dependencies
pip install -e .
pip install -e ".[dev]"  # includes test dependencies
```

---

## Local Access

| Service | Domain | Port |
|---------|--------|------|
| Api | http://ai-beta-tester-api.test | 8765 |
| Frontend | http://ai-beta-tester.test | 3080 |

Port assignments defined in `~/Development/dev/ports.json`.

---

## Commands

```bash
# Start API
source .venv/bin/activate && ai-beta-test ui --no-browser

# Start frontend
npm run dev

# Run tests
pytest

# Type checking
mypy .

# Lint
ruff check .
```

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
  napgpt_run_final/
    screenshots/
    sessions/
  solar-sync/
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

---

## Notes

- Tech: FastAPI, JavaScript, Python
