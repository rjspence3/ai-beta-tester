# Rules.md — Non-Negotiable Rules

## Safety & Permissions

- Auto-execute only read-only commands (`git status`, `ls`). Never auto-execute `git add/commit`, `rm`, destructive DB ops, or network-mutating scripts.
- Never print, store, or commit secrets/tokens/PII.
- Do not modify protected paths (`/migrations/`, `/secrets/`, `/legacy/`) unless task explicitly grants it.

---

## Planning & Workflow

- **Plan first:** produce a numbered roadmap of files/functions to touch.
- **Tests before code:** write or extend tests first; add regression tests for any bug fixed.
- **Code minimal:** implement the minimum needed to pass tests.
- **Explain decisions:** record risks, alternatives, and contract changes after coding.
- **Evidence discipline:** every claim or fix suggestion must cite `file:line`.
- Prefer **small diffs** that neutralize risk ("minimal, high-impact change").

---

## TDD & CI Gates

- Local gates (must pass before proposing diff):
    - Lint: `make lint` or equivalent
    - Typecheck: `make typecheck` or equivalent
    - Unit tests: `make test` or equivalent
- Code cannot merge with:
    - Any **critical** or **high** unresolved issue.
    - Secrets, tokens, or unredacted PII present.

---

## Contracts & Compatibility

- **Search & Reuse** existing functions/classes before creating new ones.
- Each boundary (API, queue, DB, file) must validate input/output using schemas.
- When modifying contracts, list affected consumers.
- Always enforce **timeout + retry policy** for outbound calls.

---

## Anti-Patterns (Hard Fail)

- Secrets/tokens in code or tests.
- Swallowed errors (`catch {}` / `bare except`).
- Unbounded retries or **no timeouts** on I/O.
- Ad-hoc SQL via string concat (no params).
- Tests that don't assert outcomes.
- Silent fallbacks that mask failures.

---

## PR Hygiene

- Diffs must be minimal; no drive-by refactors.
- PR description must include: purpose, plan vs. result, risk notes, test evidence.
- Use Conventional Commits.
