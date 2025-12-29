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
