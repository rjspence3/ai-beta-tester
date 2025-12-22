# AI Beta Tester - Product Requirements Document

## Overview

AI Beta Tester is an internal tool that deploys AI agents with distinct testing personalities to interact with web applications through browser automation. Each agent approaches the application differently based on their behavioral profile, surfacing bugs, UX friction, and edge cases that uniform testing would miss.

**Owner:** Rob  
**Status:** Draft  
**Last Updated:** December 2024

---

## Problem Statement

Solo developers and small teams face a testing gap: you built the thing, so you know how it's supposed to work. This makes you blind to confusion points, edge cases, and friction that real users will encounter. Traditional beta testing requires recruiting humans, coordinating schedules, and waiting for feedback. Automated testing (unit, integration, e2e) validates expected behavior but doesn't explore unexpected usage patterns.

AI Beta Tester fills this gap by simulating diverse user behaviors on demand, providing immediate feedback before shipping.

---

## Goals

1. **Reduce time-to-feedback** - Get usability insights in minutes, not days
2. **Surface blind spots** - Catch issues the developer can't see because of familiarity bias
3. **Explore edge cases** - Simulate behaviors a developer wouldn't think to test manually
4. **Create reproducible reports** - Generate actionable bug reports with screenshots and steps

## Non-Goals

- Replacing unit/integration tests (this is exploratory, not regression)
- Load testing or performance benchmarking
- Security penetration testing (though agents may incidentally find issues)
- Testing native mobile applications (web only)

---

## User Personas

The only user is Rob, using this to beta test personal projects before launch. Primary targets:

- OutSystems applications
- React/Next.js web apps
- Static sites with interactive elements
- Internal tools and dashboards

---

## Agent Personalities

Each personality is defined by behavioral parameters and a system prompt that shapes how the agent interprets and interacts with the UI.

### 1. Speedrunner
**Mindset:** "I don't have time for this."  
**Behaviors:**
- Skips tooltips, modals, and onboarding flows
- Clicks the most prominent button immediately
- Minimal reading—relies on visual hierarchy
- Abandons if something takes more than a few seconds

**Surfaces:** Missing loading states, unclear primary actions, broken fast-paths, what happens when users skip instructions

### 2. Methodical Newbie
**Mindset:** "I want to understand before I act."  
**Behaviors:**
- Reads all visible text before interacting
- Hovers over elements to check for tooltips
- Hesitates at decision points, may backtrack
- Follows instructions literally

**Surfaces:** Confusing copy, missing help text, jargon, unclear navigation, assumption gaps

### 3. Chaos Gremlin
**Mindset:** "What happens if I do this?"  
**Behaviors:**
- Inputs unexpected data (special characters, extremely long strings, empty submissions)
- Rapid back/forward navigation
- Resizes browser window mid-flow
- Clicks things multiple times
- Interrupts loading states

**Surfaces:** Input validation gaps, race conditions, responsive breakpoints, error handling, state corruption

### 4. Accessibility Auditor
**Mindset:** "Can everyone use this?"  
**Behaviors:**
- Keyboard-only navigation (no mouse)
- Checks for focus indicators
- Evaluates color contrast and text sizing
- Looks for proper ARIA labels and semantic HTML
- Tests with simulated screen reader interpretation

**Surfaces:** Accessibility violations, keyboard traps, missing labels, poor focus management

### 5. Suspicious Skeptic
**Mindset:** "Is this thing trying to trick me?"  
**Behaviors:**
- Reads fine print and disclaimers
- Hesitates at data entry fields
- Looks for privacy policies and terms
- Questions why certain permissions are requested
- Abandons if trust signals are missing

**Surfaces:** Trust gaps, unclear data usage, missing security indicators, dark patterns

---

## Functional Requirements

### FR-1: Session Management
- **FR-1.1:** User can start a test session by providing a target URL and selecting one or more agent personalities
- **FR-1.2:** User can define a goal for the session (e.g., "Complete signup flow", "Find and view a product", "Explore freely")
- **FR-1.3:** User can set session parameters: max duration, max actions, viewport size
- **FR-1.4:** Multiple agents can run in parallel against the same target

### FR-2: Browser Automation
- **FR-2.1:** System controls a browser instance via Playwright MCP
- **FR-2.2:** Supported actions: navigate, click, type, scroll, hover, screenshot, wait
- **FR-2.3:** Agent can observe current page state via screenshots and DOM inspection
- **FR-2.4:** System captures network requests and console errors during session

### FR-3: Agent Reasoning
- **FR-3.1:** Agent receives current page screenshot and determines next action based on personality and goal
- **FR-3.2:** Agent maintains short-term memory of actions taken and observations made
- **FR-3.3:** Agent can recognize when goal is achieved, when stuck, or when something unexpected occurs
- **FR-3.4:** Agent logs findings in real-time with severity classification

### FR-4: Finding Classification
Agents classify findings into categories:

| Category | Description | Example |
|----------|-------------|---------|
| **Bug** | Something is broken | Button doesn't respond to click |
| **UX Friction** | Works but confusing | Unclear what "Submit" actually does |
| **Edge Case** | Unexpected behavior under unusual input | Emoji in name field breaks display |
| **Accessibility** | Barrier for users with disabilities | No keyboard focus on modal |
| **Missing Feedback** | User left uncertain about state | No confirmation after form submit |
| **Performance** | Noticeable delay or hang | 5+ seconds to load after action |

### FR-5: Reporting
- **FR-5.1:** Each session produces a structured report (Markdown and JSON)
- **FR-5.2:** Report includes: summary, findings by severity, action log, screenshots at key moments
- **FR-5.3:** Findings include reproduction steps derived from action log
- **FR-5.4:** Cross-agent analysis highlights patterns (multiple agents struggled at same point)

### FR-6: Configuration
- **FR-6.1:** Personality prompts are stored as editable templates
- **FR-6.2:** User can create custom personalities by defining behavioral parameters
- **FR-6.3:** User can save preset configurations for specific project types

---

## Technical Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI / Interface                        │
│                 (Start session, view reports)               │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Orchestrator (Python)                    │
│         - Spawns agent sessions                             │
│         - Manages parallel execution                        │
│         - Aggregates findings                               │
└───────────┬─────────────────────────────────┬───────────────┘
            │                                 │
┌───────────▼───────────┐       ┌─────────────▼─────────────┐
│   Agent Instance      │       │     Agent Instance        │
│   ┌───────────────┐   │       │     (Personality B)       │
│   │ Personality   │   │       │                           │
│   │ Prompt        │   │       └─────────────┬─────────────┘
│   └───────┬───────┘   │                     │
│           │           │                     │
│   ┌───────▼───────┐   │                     │
│   │ Claude API    │   │                     │
│   │ (Reasoning)   │   │                     │
│   └───────┬───────┘   │                     │
│           │           │                     │
│   ┌───────▼───────┐   │                     │
│   │ Playwright    │   │                     │
│   │ MCP Client    │   │                     │
│   └───────┬───────┘   │                     │
└───────────┼───────────┘                     │
            │                                 │
┌───────────▼─────────────────────────────────▼───────────────┐
│                    Playwright MCP Server                    │
│              (Browser automation via MCP tools)             │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Browser Instance(s)                      │
│                      (Chromium)                             │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Orchestrator | Python 3.11+ | Familiar, good async support, rich ecosystem |
| LLM | Claude API (Sonnet) | Cost-effective for high-volume agent calls, strong vision |
| Browser Automation | Playwright MCP | MCP-native, full browser control, screenshot capability |
| Configuration | YAML files | Human-readable, easy to version control |
| Reports | Markdown + JSON | Markdown for reading, JSON for programmatic analysis |
| Storage | Local filesystem | No database needed for internal tool |

### Playwright MCP Integration

The system will use a Playwright MCP server that exposes browser automation as tools. Key tools required:

- `browser_navigate(url)` - Go to URL
- `browser_screenshot()` - Capture current viewport
- `browser_click(selector | coordinates)` - Click element
- `browser_type(selector, text)` - Enter text in field
- `browser_scroll(direction, amount)` - Scroll page
- `browser_get_text(selector)` - Extract text content
- `browser_wait(condition)` - Wait for element or state

Agent reasoning loop:
1. Take screenshot
2. Send screenshot + context to Claude
3. Claude returns next action as tool call
4. Execute tool via MCP
5. Observe result, update context
6. Repeat

---

## Data Model

### Session
```yaml
session:
  id: uuid
  target_url: string
  goal: string
  started_at: timestamp
  ended_at: timestamp
  status: running | completed | failed
  config:
    max_duration_seconds: int
    max_actions: int
    viewport: { width: int, height: int }
  agents: [AgentRun]
```

### AgentRun
```yaml
agent_run:
  id: uuid
  session_id: uuid
  personality: string
  status: running | completed | stuck | failed
  actions: [Action]
  findings: [Finding]
  started_at: timestamp
  ended_at: timestamp
```

### Action
```yaml
action:
  sequence: int
  timestamp: timestamp
  type: navigate | click | type | scroll | screenshot | wait
  parameters: object
  result: success | failed
  screenshot_path: string (optional)
  observation: string (agent's interpretation)
```

### Finding
```yaml
finding:
  id: uuid
  agent_run_id: uuid
  timestamp: timestamp
  category: bug | ux_friction | edge_case | accessibility | missing_feedback | performance
  severity: critical | high | medium | low
  title: string
  description: string
  screenshot_path: string
  reproduction_steps: [string]
  action_sequence: [int] (references actions that led to finding)
```

---

## User Interface

### Phase 1: CLI
Simple command-line interface for running sessions and viewing reports.

```bash
# Start a session with default personalities
ai-beta-test run https://myapp.com --goal "Complete user registration"

# Start with specific personalities
ai-beta-test run https://myapp.com --agents speedrunner,chaos_gremlin

# View latest report
ai-beta-test report --latest

# List past sessions
ai-beta-test sessions
```

### Phase 2: Web Dashboard (Future)
If the tool proves valuable, a simple local web UI could provide:
- Visual session configuration
- Real-time agent activity view
- Interactive report browsing
- Screenshot galleries

---

## Report Format

### Summary Section
```markdown
# Beta Test Report: MyApp Registration Flow
**Target:** https://myapp.com/register  
**Goal:** Complete user registration  
**Date:** 2024-12-15  
**Duration:** 4m 32s  

## Agents
| Personality | Status | Actions | Findings |
|-------------|--------|---------|----------|
| Speedrunner | Completed | 12 | 2 |
| Methodical Newbie | Completed | 28 | 4 |
| Chaos Gremlin | Stuck | 15 | 3 |

## Summary
3 agents tested the registration flow. The Chaos Gremlin got stuck on the 
email validation step when entering special characters. Common friction 
point: 2/3 agents hesitated at the password requirements (not visible 
until after first failed attempt).
```

### Findings Section
```markdown
## Findings

### Critical (1)

#### [BUG] Form submits with empty required fields
**Found by:** Chaos Gremlin  
**Severity:** Critical  

The registration form allows submission when the "Company" field is empty 
despite being marked as required. Server returns 500 error.

**Reproduction Steps:**
1. Navigate to /register
2. Fill email and password fields
3. Leave Company field empty
4. Click Submit

**Screenshot:** ![](./screenshots/session_abc123/finding_001.png)

---

### High (2)
...
```

---

## Success Metrics

Since this is an internal tool, success is measured by practical utility:

1. **Adoption:** Do I actually use this before shipping projects?
2. **Discovery rate:** Does it find issues I wouldn't have caught manually?
3. **Time saved:** Is running AI beta test faster than manual exploration?
4. **Fix rate:** Do I actually fix the issues it surfaces?

Lightweight tracking: keep a log of findings and which ones led to changes.

---

## Development Phases

### Phase 1: Foundation (MVP)
- [ ] Set up Playwright MCP server
- [ ] Build basic orchestrator that runs single agent
- [ ] Implement one personality (Speedrunner)
- [ ] Create agent reasoning loop with Claude
- [ ] Generate basic Markdown report
- [ ] CLI to start session and view report

**Exit Criteria:** Can run a single agent against a URL and get a useful report

### Phase 2: Multi-Personality
- [ ] Implement remaining 4 personalities
- [ ] Parallel agent execution
- [ ] Cross-agent pattern detection in reports
- [ ] Finding deduplication

**Exit Criteria:** Can run all 5 personalities in parallel, report highlights common friction points

### Phase 3: Polish
- [ ] Custom personality creation
- [ ] Session presets for project types
- [ ] Improved screenshot capture (key moments, not every action)
- [ ] Action replay capability
- [ ] Export to GitHub Issues format

**Exit Criteria:** Tool is streamlined enough to use without friction on every project

### Phase 4: Optional Enhancements
- [ ] Local web dashboard
- [ ] Integration with OutSystems preview URLs
- [ ] Comparison mode (test before/after changes)
- [ ] Finding history across sessions

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Agent gets stuck in loops | High | Medium | Max action limit, loop detection, stuck state recognition |
| Vision model misinterprets UI | Medium | Medium | Supplement screenshots with DOM inspection, allow human hints |
| Cost of Claude API calls | Medium | Low | Use Sonnet for routine actions, Opus only for complex reasoning |
| Playwright MCP instability | Medium | High | Evaluate MCP implementations carefully, have fallback to direct Playwright |
| Too many low-value findings | Medium | Medium | Tunable severity thresholds, finding deduplication |

---

## Open Questions

1. **Which Playwright MCP implementation?** Need to evaluate community options for reliability and feature completeness.

2. **How to handle authentication?** For apps requiring login, should the agent be provided credentials, or should authenticated state be set up before the session?

3. **Handling SPAs and dynamic content?** Need strategy for waiting on React/Vue renders, loading states, etc.

4. **Screenshot strategy?** Every action creates many images. Need balance between coverage and storage/cost.

5. **Goal completion detection?** How does the agent know when it's "done"? Success indicators vs. max actions fallback.

---

## Appendix: Personality Prompt Templates

### Speedrunner
```
You are beta testing a web application as a Speedrunner—an impatient power user 
who has no time to waste.

Your behavioral traits:
- You SKIP any tutorials, tooltips, modals, or onboarding flows immediately
- You look for the most prominent action and click it without reading surrounding text
- You rely on visual hierarchy: big buttons, bright colors, obvious CTAs
- If something takes more than 3 seconds to load, you note it as a problem
- You don't read instructions; you figure things out by clicking
- You get frustrated by unnecessary steps or confirmations

Your goal: {goal}

As you navigate, report any issues you encounter:
- Bugs: Things that are clearly broken
- Friction: Things that slow you down unnecessarily  
- Confusion: Places where the fast path isn't obvious

Think like someone who uses apps all day and has zero patience for bad UX.
```

### Chaos Gremlin
```
You are beta testing a web application as a Chaos Gremlin—a mischievous tester 
who tries to break things.

Your behavioral traits:
- You enter unexpected inputs: special characters, emojis, extremely long strings, 
  SQL injection attempts, empty submissions, negative numbers where positives expected
- You click things multiple times rapidly
- You use the back button at unexpected moments
- You interrupt loading states by clicking elsewhere
- You resize the browser window to unusual dimensions
- You try to access things you shouldn't have access to
- You submit forms with missing required fields

Your goal: {goal} (but really, your goal is to find what breaks)

As you navigate, report any issues you encounter:
- Edge cases: Unexpected behavior under unusual conditions
- Validation gaps: Inputs that should be rejected but aren't
- Error handling: Poor or missing error messages
- State corruption: When the app gets into a weird state

Think like someone trying to find bugs before malicious users do.
```

---

## References

- [Playwright MCP Server (Community)](https://github.com/anthropics/anthropic-quickstarts)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Claude Vision Documentation](https://docs.anthropic.com/claude/docs/vision)
- [Browser Use Library](https://github.com/browser-use/browser-use)
