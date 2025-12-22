# Contributing to AI Beta Tester

## Development Setup

```bash
# Clone and setup
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Verify
mypy src/ai_beta_tester --ignore-missing-imports
ruff check src/ai_beta_tester
```

## Code Quality

Before committing:

```bash
# Type checking (strict mode)
mypy src/ai_beta_tester --ignore-missing-imports

# Linting
ruff check src/ai_beta_tester

# Auto-fix lint issues
ruff check src/ai_beta_tester --fix
```

## Project Structure

```
src/ai_beta_tester/
├── __init__.py             # Package version
├── cli.py                  # Typer CLI commands
├── orchestrator.py         # Core SDK integration
├── models/
│   ├── __init__.py         # Model exports
│   ├── session.py          # Session + SessionConfig
│   ├── agent_run.py        # AgentRun tracking
│   ├── action.py           # Action types and logging
│   └── finding.py          # Finding categories/severities
├── personalities/
│   ├── __init__.py         # Personality exports
│   ├── base.py             # Personality ABC + registry
│   ├── speedrunner.py      # Speedrunner implementation
│   └── chaos_gremlin.py    # Chaos Gremlin implementation
└── reporting/
    ├── __init__.py         # Reporter exports
    └── markdown.py         # Markdown report generator
```

## Adding a New Personality

1. Create a new file in `personalities/`:

```python
# src/ai_beta_tester/personalities/methodical_newbie.py
"""Methodical Newbie personality - reads everything carefully."""

from ai_beta_tester.personalities.base import Personality, register_personality


@register_personality
class MethodicalNewbiePersonality(Personality):
    """A cautious user who reads all text before acting."""

    name = "methodical_newbie"
    description = "Cautious user who reads everything and follows instructions literally"
    mindset = "I want to understand before I act."

    @classmethod
    def get_system_prompt(cls, goal: str) -> str:
        return f"""You are beta testing a web application as a Methodical Newbie...

## Your Mindset
"{cls.mindset}"

## Your Behavioral Traits
- Read all visible text before interacting
- Hover over elements to check for tooltips
- Hesitate at decision points, may backtrack
- Follow instructions literally
...

## Your Goal
{goal}

{cls.get_finding_prompt_section()}
"""
```

2. Import in `personalities/__init__.py`:

```python
from ai_beta_tester.personalities.methodical_newbie import MethodicalNewbiePersonality
```

3. The `@register_personality` decorator automatically adds it to the registry.

## Key Classes

### Orchestrator

The `Orchestrator` class manages test sessions:

```python
orchestrator = Orchestrator(OrchestratorConfig())
session = await orchestrator.run_session(
    target_url="https://example.com",
    goal="Complete signup",
    personalities=["speedrunner", "chaos_gremlin"],
)
```

Internally uses `ClaudeSDKClient` for continuous conversations with the Claude API.

### Session Models

```python
# Session contains multiple agent runs
session = Session(target_url="...", goal="...")
session.start()

# Each personality gets its own AgentRun
agent_run = AgentRun(session_id=session.id, personality="speedrunner")
agent_run.actions.append(Action(...))
agent_run.findings.append(Finding(...))
```

### ClaudeAgentOptions

The orchestrator configures the SDK:

```python
options = ClaudeAgentOptions(
    system_prompt=personality_prompt,
    mcp_servers={
        "playwright": {
            "command": "npx",
            "args": ["@anthropic-ai/mcp-server-playwright"],
        }
    },
    allowed_tools=[...],  # Playwright MCP tools
    permission_mode="bypassPermissions",
    max_turns=50,
    model="sonnet",
)
```

## Testing Against Real Sites

For development, use sites that won't block automated access:

```bash
# Playwright's demo site
ai-beta-test run https://demo.playwright.dev/todomvc -g "Add three todo items"

# HTTPBin for edge cases
ai-beta-test run https://httpbin.org/forms/post -g "Submit the form"
```

## MCP Tool Reference

The Playwright MCP server exposes these tools (prefixed `mcp__playwright__`):

| Tool | Purpose |
|------|---------|
| `browser_navigate` | Go to URL |
| `browser_snapshot` | Get accessibility tree (preferred for actions) |
| `browser_click` | Click element |
| `browser_type` | Enter text |
| `browser_scroll` | Scroll page |
| `browser_hover` | Hover over element |
| `browser_take_screenshot` | Capture viewport |
| `browser_press_key` | Keyboard input |
| `browser_select_option` | Dropdown selection |
| `browser_wait_for` | Wait for condition |

## Finding Extraction

Currently uses heuristic text matching in `_extract_findings_from_text()`. For more reliable extraction, consider using the SDK's structured output feature:

```python
options = ClaudeAgentOptions(
    output_format={
        "type": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "findings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string"},
                            "severity": {"type": "string"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                        }
                    }
                }
            }
        }
    }
)
```

## Debugging

Enable verbose output by checking `ResultMessage` details:

```python
if isinstance(message, ResultMessage):
    print(f"Duration: {message.duration_ms}ms")
    print(f"Cost: ${message.total_cost_usd}")
    print(f"Turns: {message.num_turns}")
```

For MCP issues, run the Playwright server directly:

```bash
npx @anthropic-ai/mcp-server-playwright
```

## Phase 2 Roadmap

From the PRD:

- [ ] Implement remaining personalities (Methodical Newbie, Accessibility Auditor, Suspicious Skeptic)
- [ ] Parallel agent execution
- [ ] Cross-agent pattern detection
- [ ] Finding deduplication
- [ ] Custom personality creation via YAML
