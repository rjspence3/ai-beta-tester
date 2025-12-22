# AI Beta Tester

AI-powered exploratory web testing with distinct agent personalities. Each agent approaches your application differently based on behavioral traits, surfacing bugs, UX friction, and edge cases that uniform testing would miss.

## Problem

You built the thing, so you know how it's supposed to work. This makes you blind to confusion points, edge cases, and friction that real users encounter. AI Beta Tester fills this gap by simulating diverse user behaviors on demand.

## Features

- **Personality-driven testing** - Agents with distinct behavioral profiles (impatient users, chaos testers, etc.)
- **Browser automation** - Full Playwright-powered interaction via MCP
- **Structured findings** - Categorized issues with reproduction steps
- **Markdown reports** - Actionable output for every session

## Prerequisites

- Python 3.11+
- Node.js 18+ (for Playwright MCP server)
- Anthropic API key

## Installation

```bash
# Clone and enter the project
cd ai-beta-tester

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install the package
pip install -e .

# Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

Verify installation:

```bash
ai-beta-test --help
```

## Quick Start

Run a test session:

```bash
ai-beta-test run https://your-app.com --goal "Complete the signup flow"
```

This launches the default `speedrunner` personality against your target URL.

## Usage

### Run a Test Session

```bash
ai-beta-test run <URL> [OPTIONS]
```

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--goal` | `-g` | Goal for the test session | "Explore the application and find issues" |
| `--agents` | `-a` | Comma-separated personalities | speedrunner |
| `--max-actions` | | Maximum actions per agent | 50 |
| `--max-duration` | | Maximum duration in seconds | 300 |
| `--output` | `-o` | Output directory for reports | ./reports |

**Examples:**

```bash
# Test with a specific goal
ai-beta-test run https://myapp.com -g "Add item to cart and checkout"

# Run multiple personalities
ai-beta-test run https://myapp.com -a speedrunner,chaos_gremlin

# Limit actions for quick scan
ai-beta-test run https://myapp.com --max-actions 20
```

### List Available Personalities

```bash
ai-beta-test personalities
```

### View Reports

```bash
# Show the latest report
ai-beta-test report --latest

# List all reports
ai-beta-test report
```

## Agent Personalities

### Speedrunner

**Mindset:** "I don't have time for this."

- Skips tutorials, tooltips, and onboarding
- Clicks the most prominent button immediately
- Relies on visual hierarchy, minimal reading
- Gets frustrated by slow responses or extra steps

**Surfaces:** Missing loading states, unclear primary actions, broken fast-paths

### Chaos Gremlin

**Mindset:** "What happens if I do this?"

- Enters unexpected inputs (special chars, emojis, long strings)
- Clicks things multiple times rapidly
- Uses back button at unexpected moments
- Submits forms with missing required fields

**Surfaces:** Input validation gaps, error handling issues, state corruption

### Coming Soon

- **Methodical Newbie** - Reads everything, follows instructions literally
- **Accessibility Auditor** - Keyboard-only navigation, screen reader evaluation
- **Suspicious Skeptic** - Looks for trust signals, reads fine print

## Finding Categories

| Category | Description |
|----------|-------------|
| **Bug** | Something is broken (button doesn't respond, crashes) |
| **UX Friction** | Works but confusing (unclear labels, too many steps) |
| **Edge Case** | Unexpected behavior under unusual conditions |
| **Accessibility** | Barriers for users with disabilities |
| **Missing Feedback** | User left uncertain about state |
| **Performance** | Noticeable delay (>3 seconds) |

## Report Format

Each session generates a Markdown report in `./reports/`:

```markdown
# Beta Test Report: Complete signup flow

**Target:** https://myapp.com
**Goal:** Complete signup flow
**Duration:** 2m 34s

## Agents

| Personality | Status | Actions | Findings |
|-------------|--------|---------|----------|
| Speedrunner | Completed | 15 | 2 |

## Findings

### High (1)

#### [BUG] Form submits with empty required fields
**Found by:** Speedrunner
**Severity:** High

The registration form allows submission when the "Company" field is empty.

---

## Action Log

### Speedrunner

1. Navigate to https://myapp.com
2. Click on Sign Up button
3. Type 'test@example.com' into Email field
...
```

## Architecture

```
src/ai_beta_tester/
├── cli.py              # Typer-based command interface
├── orchestrator.py     # ClaudeSDKClient + session management
├── models/             # Session, AgentRun, Action, Finding
├── personalities/      # Registered personality classes
└── reporting/          # Markdown report generation
```

The orchestrator uses the Claude Agent SDK with `ClaudeSDKClient` for continuous conversations. Each agent run spawns a Playwright MCP server for browser automation.

## Configuration

### Session Defaults

Edit `src/ai_beta_tester/models/session.py`:

```python
@dataclass
class SessionConfig:
    max_duration_seconds: int = 300
    max_actions: int = 50
    viewport_width: int = 1280
    viewport_height: int = 720
```

### Model Selection

The orchestrator defaults to Claude Sonnet. Edit `src/ai_beta_tester/orchestrator.py`:

```python
@dataclass
class OrchestratorConfig:
    model: str = "sonnet"  # or "opus", "haiku"
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run type checking
mypy src/ai_beta_tester

# Run linting
ruff check src/ai_beta_tester

# Run tests
pytest
```

## Troubleshooting

### "npx: command not found"

Install Node.js 18+ from https://nodejs.org or via your package manager:

```bash
# macOS
brew install node

# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### "Playwright browser not installed"

The Playwright MCP server should install browsers automatically. If not:

```bash
npx playwright install chromium
```

### Agent gets stuck in loops

Reduce `--max-actions` or make the goal more specific. The agent has loop detection but complex SPAs can confuse it.

### Rate limiting

For high-volume testing, consider using Claude Haiku by editing the orchestrator config.

## License

Internal tool - not for redistribution.

## References

- [Claude Agent SDK Documentation](https://docs.anthropic.com/en/docs/agent-sdk/overview)
- [Playwright MCP Server](https://github.com/anthropics/anthropic-quickstarts)
- [PRD](./docs/ai-beta-tester-prd.md)
