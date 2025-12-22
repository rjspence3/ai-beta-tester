# Architecture

## Overview

AI Beta Tester uses the Claude Agent SDK to coordinate AI agents that test web applications through browser automation. Each agent embodies a distinct "personality" that shapes how it interacts with the UI.

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI                                 │
│                    (ai-beta-test)                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Orchestrator                             │
│         - Creates sessions                                  │
│         - Spawns agent runs per personality                 │
│         - Aggregates findings into reports                  │
└───────────┬─────────────────────────────────┬───────────────┘
            │                                 │
┌───────────▼───────────┐       ┌─────────────▼─────────────┐
│   Agent Run           │       │     Agent Run             │
│   (Speedrunner)       │       │     (Chaos Gremlin)       │
│   ┌───────────────┐   │       │                           │
│   │ Personality   │   │       └─────────────┬─────────────┘
│   │ System Prompt │   │                     │
│   └───────┬───────┘   │                     │
│           │           │                     │
│   ┌───────▼───────┐   │                     │
│   │ClaudeSDKClient│   │                     │
│   │ (Agent Loop)  │   │                     │
│   └───────┬───────┘   │                     │
│           │           │                     │
│   ┌───────▼───────┐   │                     │
│   │ Playwright    │   │                     │
│   │ MCP Server    │   │                     │
│   └───────┬───────┘   │                     │
└───────────┼───────────┘                     │
            │                                 │
┌───────────▼─────────────────────────────────▼───────────────┐
│                    Browser Instance                         │
│                      (Chromium)                             │
└─────────────────────────────────────────────────────────────┘
```

## Components

### CLI (`cli.py`)

Typer-based command interface with three commands:

- `run` - Execute a test session
- `personalities` - List available agent personalities
- `report` - View generated reports

Entry point defined in `pyproject.toml`:
```toml
[project.scripts]
ai-beta-test = "ai_beta_tester.cli:app"
```

### Orchestrator (`orchestrator.py`)

Core coordination logic:

1. **Session creation** - Initializes `Session` with target URL and goal
2. **Agent spawning** - Creates `AgentRun` for each personality
3. **SDK integration** - Configures `ClaudeSDKClient` with MCP servers
4. **Finding aggregation** - Collects findings from agent responses

Key SDK usage:

```python
async with ClaudeSDKClient(options=options) as client:
    await client.query(initial_prompt)

    async for message in client.receive_messages():
        if isinstance(message, AssistantMessage):
            # Extract actions and findings from content blocks
        if isinstance(message, ResultMessage):
            # Session complete
```

### Personalities (`personalities/`)

Each personality is a class that:

1. Inherits from `Personality` base class
2. Registers via `@register_personality` decorator
3. Implements `get_system_prompt(goal)` method

The system prompt shapes agent behavior through:
- Mindset description
- Behavioral traits
- What to look for
- How to report findings

Registry pattern allows dynamic personality loading:

```python
_PERSONALITY_REGISTRY: dict[str, type[Personality]] = {}

def get_personality(name: str) -> type[Personality]:
    return _PERSONALITY_REGISTRY[name]
```

### Models (`models/`)

Data structures for session tracking:

```
Session
├── id: UUID
├── target_url: str
├── goal: str
├── config: SessionConfig
├── status: SessionStatus
└── agent_runs: list[AgentRun]
        ├── id: UUID
        ├── personality: str
        ├── status: AgentRunStatus
        ├── actions: list[Action]
        │       ├── action_type: ActionType
        │       ├── parameters: dict
        │       └── observation: str
        └── findings: list[Finding]
                ├── category: FindingCategory
                ├── severity: FindingSeverity
                ├── title: str
                └── description: str
```

### Reporting (`reporting/`)

`MarkdownReporter` generates structured reports:

1. **Header** - Target, goal, date, duration
2. **Agent summary** - Table of personalities and their results
3. **Findings** - Grouped by severity
4. **Action log** - Step-by-step reproduction trail

## Data Flow

### 1. Session Initialization

```
CLI (run command)
    │
    ├─► Validate personalities against registry
    ├─► Create Session with config
    └─► Pass to Orchestrator.run_session()
```

### 2. Agent Execution

```
Orchestrator._run_agent()
    │
    ├─► Create AgentRun
    ├─► Get personality system prompt
    ├─► Configure ClaudeAgentOptions
    │       ├─► system_prompt (from personality)
    │       ├─► mcp_servers (Playwright)
    │       ├─► allowed_tools (browser actions)
    │       └─► max_turns (from session config)
    │
    └─► Run agent loop via ClaudeSDKClient
            │
            ├─► Send initial prompt (URL + goal)
            │
            └─► Process messages:
                    ├─► ToolUseBlock → Action
                    ├─► TextBlock → Finding extraction
                    └─► ResultMessage → Complete
```

### 3. Finding Extraction

Current implementation uses heuristic keyword matching:

```python
finding_keywords = {
    "BUG": FindingCategory.BUG,
    "UX_FRICTION": FindingCategory.UX_FRICTION,
    ...
}

# Scan agent text for category keywords
for keyword, category in finding_keywords.items():
    if keyword in text.upper():
        # Create Finding with extracted details
```

This is intentionally simple for MVP. Phase 2 could use structured output.

### 4. Report Generation

```
Session
    │
    └─► MarkdownReporter.generate()
            │
            ├─► Format header (target, goal, duration)
            ├─► Build agent summary table
            ├─► Group findings by severity
            ├─► Format action logs
            └─► Return markdown string
```

## MCP Integration

The Playwright MCP server provides browser automation:

```python
mcp_servers={
    "playwright": {
        "command": "npx",
        "args": ["@anthropic-ai/mcp-server-playwright"],
    }
}
```

Tools are namespaced as `mcp__playwright__*`:

| Tool | Maps to ActionType |
|------|-------------------|
| `browser_navigate` | NAVIGATE |
| `browser_click` | CLICK |
| `browser_type` | TYPE |
| `browser_scroll` | SCROLL |
| `browser_hover` | HOVER |
| `browser_take_screenshot` | SCREENSHOT |
| `browser_snapshot` | SCREENSHOT |
| `browser_press_key` | PRESS_KEY |
| `browser_select_option` | SELECT |
| `browser_wait_for` | WAIT |

## Configuration Points

### OrchestratorConfig

```python
@dataclass
class OrchestratorConfig:
    sessions_dir: Path = Path("./sessions")
    screenshots_dir: Path = Path("./screenshots")
    model: str = "sonnet"  # Claude model selection
```

### SessionConfig

```python
@dataclass
class SessionConfig:
    max_duration_seconds: int = 300
    max_actions: int = 50
    viewport_width: int = 1280
    viewport_height: int = 720
```

### ClaudeAgentOptions

Configured per agent run:

```python
ClaudeAgentOptions(
    system_prompt=...,           # From personality
    mcp_servers=...,             # Playwright
    allowed_tools=[...],         # Browser actions only
    permission_mode="bypassPermissions",
    max_turns=50,
    model="sonnet",
)
```

## Error Handling

Agent failures are captured as findings:

```python
except Exception as e:
    agent_run.fail()
    agent_run.findings.append(
        Finding(
            category=FindingCategory.BUG,
            severity=FindingSeverity.HIGH,
            title="Agent execution failed",
            description=str(e),
        )
    )
```

This ensures session results are always available even when agents crash.

## Future Considerations

### Parallel Execution (Phase 2)

Current implementation runs personalities sequentially. Parallel execution would:

1. Use `asyncio.gather()` for concurrent agent runs
2. Require separate browser instances per agent
3. Enable cross-agent pattern detection (multiple agents stuck at same point)

### Structured Output (Phase 2)

Replace heuristic finding extraction with SDK's `OutputFormat`:

```python
output_format={
    "type": "json_schema",
    "schema": finding_schema
}
```

### Custom Personalities (Phase 3)

Load personalities from YAML files:

```yaml
# personalities/custom.yaml
name: custom_tester
description: My custom testing approach
mindset: "..."
behavioral_traits:
  - ...
```
