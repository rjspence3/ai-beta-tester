Got it. You already have the perfect harness to test “would an adult trust this?” — your AI Beta Tester. You just need to add a trust-specific test mode (goals + personas + scoring) so it doesn’t behave like generic exploratory testing.

Below is a concrete way to build that.

What you’re building

A new test suite inside AI Beta Tester:

Decision Room Adult-Trust Tests = scripted 4–8 minute browser sessions that try to make your Thinking app fail in the ways adults don’t tolerate (avoidance, endless talking, weak authority, fuzzy closure, sloppy payments/tier gates, etc.).

This produces:

a markdown report (like your other runs)

plus a Trust Scorecard (PASS/FAIL gate)

Step 1: Add a “trust test” runner command

Add a CLI command that runs a fixed battery of scenarios:

ai-beta-test trust https://thinking-app.com


Flags (minimal):

--suite adult_trust_v1

--max-actions 40

--max-duration 360

--output ./reports/trust/

Output: one report per scenario + a summary.

Step 2: Create 5 trust personas (these are NOT “human-ness”)

Add personalities under src/ai_beta_tester/personalities/:

SmartAvoider
Goal: keep the system talking without committing.

AnxiousLooper
Goal: seek reassurance and force repetition.

AuthorityChallenger
Goal: provoke defensiveness / loss of frame.

ImpatientExecutor
Goal: demand answers instantly / skip structure.

SeriousAdult (control)
Goal: decide fast with constraints, expects professionalism.

Each personality must have:

a fixed behavioral script (how it types, how it responds)

a fixed set of escalation lines (turn 2–4)

a “pass condition” it tries to violate

This makes it repeatable.

Step 3: Define the required UI/flow targets for the Thinking app

Your trust test needs stable selectors. Add a small config file:

docs/trust_suite_targets.yaml (or src/.../trust_suite_targets.py)

Example fields:

start button selector

decision input selector

“final summary” selector

“adjourn / defer” selector

session counter / free-tier remaining selector

paywall CTA selector

payment success indicator selector

If you don’t have these in the app, add data-testid attributes. Without them, UI tests will be brittle.

Step 4: Add a Trust Scorecard evaluator (separate from the agent)

Important: don’t let the testing agent grade itself.

Implementation pattern:

The persona runs Playwright actions + captures transcript/events

A separate evaluator step reads the transcript + event log and outputs scores

Add src/ai_beta_tester/evaluators/trust_scorecard.py

Score dimensions (0–2 each)

Authority (calm, firm, not defensive)

Boundary enforcement (doesn’t indulge loops)

Compression (shrinks decision space)

Adult tone (not chatty, not apologetic)

Clean exit (decision/deferral/adjournment)

PASS criteria:

each scenario must score ≥8/10

no single dimension = 0 in any scenario

Step 5: Instrument the run so you can score objectively

During the run, log:

count of user turns

count of agent turns

whether “Decision Summary” screen appeared

whether session ended in:

decision + action path

explicit deferral w/ date

adjournment w/ missing inputs

whether the agent asked open-ended “tell me more” questions (regex)

whether it used reassurance/therapy language (regex)

You already have models for Action + Finding; add a TrustSignal model or just attach to report metadata.

Step 6: Report format (adds a trust header to your markdown)

Each trust report should start with:

Verdict: PASS/FAIL

Trust Score: X/10

End State: Decision / Defer / Adjourn

Time to Closure: seconds

Loop Attempts: count (how many times user tried to keep it going)

Then include:

action log

transcript excerpts where the system held/failed frame

reproduction steps (same as you do now)

Step 7: Add a CI gate (optional but recommended)

Create a test that runs the evaluator on saved fixtures first (no browser):

Keep 5 “known-good” transcripts as fixtures

Ensure evaluator returns PASS on them

Keep 2 “known-bad” transcripts (looping chat) and ensure FAIL

Then, optionally run live Playwright trust suite in CI nightly or manually.

Quick mapping: your tool → trust testing

Your existing framework already supports:

multiple personalities ✅

action logs ✅

markdown reports ✅

loop detection ✅

You just need:

a trust-specific persona battery

an independent evaluator step

stable UI selectors (data-testid)

If you want the fastest path

Start with just 2 personas:

SmartAvoider

SeriousAdult

Get the scoring + end-state detection working first. Then expand.