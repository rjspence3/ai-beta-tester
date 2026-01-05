"""Orchestrator for managing test sessions with AI agent personalities."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable
from uuid import UUID

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    tool,
)

# Type alias for event callback
EventCallback = Callable[[str, dict], Awaitable[None]] | None

from ai_beta_tester.models import (
    Action,
    ActionType,
    AgentRun,
    Finding,
    FindingCategory,
    FindingSeverity,
    Session,
    SessionConfig,
)
from ai_beta_tester.models.agent_run import AgentRunStatus
from ai_beta_tester.personalities import get_personality, list_personalities
from ai_beta_tester.security import NavigationGuard
from ai_beta_tester.models.rubric import AgentVerdict, CognitiveLoad
from ai_beta_tester.scoring.score_run import calculate_agent_score
from ai_beta_tester.scoring.aggregate import calculate_aggregate_score


# Define the structured finding tool
@tool(
    name="report_finding",
    description="Report a specific finding (bug, UX issue, etc) discovered during testing.",
    input_schema={
        "category": str,
        "severity": str,
        "title": str,
        "description": str
    }
)
async def report_finding_tool(args: dict) -> dict:
    """Record a finding."""
    # This is a dummy implementation for the SDK.
    # The actual processing happens in the Orchestrator loop by inspecting ToolUseBlocks.
    return {"content": [{"type": "text", "text": "Finding recorded."}]}


@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator."""

    sessions_dir: Path = Path("./sessions")
    screenshots_dir: Path = Path("./screenshots")
    model: str = "sonnet"


class Orchestrator:
    """Manages test sessions and coordinates agent personalities."""

    def __init__(self, config: OrchestratorConfig | None = None) -> None:
        self.config = config or OrchestratorConfig()
        self.config.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.config.screenshots_dir.mkdir(parents=True, exist_ok=True)

    async def run_session(
        self,
        target_url: str,
        goal: str,
        personalities: list[str] | None = None,
        session_config: SessionConfig | None = None,
        event_callback: EventCallback = None,
    ) -> Session:
        """Run a test session with specified personalities.

        Args:
            target_url: The URL to test (e.g., "https://myapp.com").
            goal: What the agent should try to accomplish (e.g., "Complete signup").
            personalities: List of personality names to run. Defaults to ["speedrunner"].
            session_config: Optional configuration for timeouts and limits.
            event_callback: Optional async callback for real-time event notifications.
                Signature: async (event_type: str, data: dict) -> None

        Returns:
            Session object containing all agent runs and their findings.

        Raises:
            ValueError: If an unknown personality name is provided.
            SecurityViolation: If the target_url is blocked.
        """
        # Validate target URL security
        NavigationGuard.validate_url(target_url)

        session = Session(
            target_url=target_url,
            goal=goal,
            config=session_config or SessionConfig(),
        )
        session.start()

        # Default to speedrunner if no personalities specified
        personality_names = personalities or ["speedrunner"]

        # Validate personalities
        available = list_personalities()
        for name in personality_names:
            if name not in available:
                raise ValueError(f"Unknown personality '{name}'. Available: {available}")

        # Run each personality sequentially with delay to avoid API rate limits
        for i, personality_name in enumerate(personality_names):
            # Add delay between agents (skip for first agent)
            if i > 0 and session.config.agent_delay_seconds > 0:
                await asyncio.sleep(session.config.agent_delay_seconds)
            # Emit agent started event
            if event_callback:
                await event_callback("agent_started", {
                    "personality": personality_name,
                    "agent_index": len(session.agent_runs),
                    "total_agents": len(personality_names),
                })

            agent_run = await self._run_agent(
                session=session,
                personality_name=personality_name,
                event_callback=event_callback,
            )
            session.agent_runs.append(agent_run)

            # Emit agent completed event
            if event_callback:
                await event_callback("agent_completed", {
                    "personality": personality_name,
                    "status": agent_run.status.value,
                    "action_count": agent_run.action_count,
                    "finding_count": agent_run.finding_count,
                })

        session.complete()
        
        # Calculate aggregate session score and metrics
        session.aggregate_score = calculate_aggregate_score(session)
        
        return session

    async def _run_agent(
        self,
        session: Session,
        personality_name: str,
        event_callback: EventCallback = None,
    ) -> AgentRun:
        """Run a single agent personality against the target.

        Spawns a Playwright MCP server and runs the agent loop until completion,
        max_turns is reached, or an error occurs. Findings are extracted from
        the agent's text responses using heuristic keyword matching.

        Note:
            Uses permission_mode="bypassPermissions" because this is an automated
            testing tool where human approval for each browser action would defeat
            the purpose. The agent only has access to browser tools, not filesystem.
        """
        agent_run = AgentRun(
            session_id=session.id,
            personality=personality_name,
        )
        agent_run.start()

        personality_cls = get_personality(personality_name)
        system_prompt = personality_cls.get_system_prompt(session.goal)

        # Create an in-process MCP server for the report_finding tool
        findings_server = create_sdk_mcp_server(
            name="findings",
            tools=[report_finding_tool],
        )

        # Configure the agent with Playwright MCP for browser automation
        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            mcp_servers={
                "playwright": {
                    "command": "npx",
                    "args": ["@executeautomation/playwright-mcp-server"],
                },
                "findings": findings_server,
            },
            allowed_tools=[
                # Playwright browser tools
                "playwright_navigate",
                "playwright_screenshot",
                "playwright_click",
                "playwright_fill",
                "playwright_select",
                "playwright_hover",
                "playwright_press_key",
                "playwright_evaluate",
                # Findings tool
                "report_finding",
            ],
            permission_mode="bypassPermissions",
            max_turns=session.config.max_actions,
            model=self.config.model,
        )

        # Special configuration for Hybrid Auditor: Add Filesystem MCP
        if personality_name == "hybrid_auditor":
            # Use source_dir from session config if provided, else current directory
            source_dir = getattr(session.config, "source_dir", None) or "."
            # Add filesystem server
            options.mcp_servers["filesystem"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", source_dir],
            }
            # Add filesystem tools (MCP server-filesystem tool names)
            # Tools may be prefixed with "filesystem_" by the SDK
            options.allowed_tools.extend([
                # Unprefixed names
                "read_text_file",
                "read_multiple_files",
                "read_media_file",
                "write_file",
                "create_directory",
                "list_directory",
                "directory_tree",
                "move_file",
                "search_files",
                "get_file_info",
                "list_allowed_directories",
                # Prefixed names (in case SDK prefixes with server name)
                "filesystem_read_text_file",
                "filesystem_read_multiple_files",
                "filesystem_read_media_file",
                "filesystem_write_file",
                "filesystem_create_directory",
                "filesystem_list_directory",
                "filesystem_directory_tree",
                "filesystem_move_file",
                "filesystem_search_files",
                "filesystem_get_file_info",
                "filesystem_list_allowed_directories",
            ])

        # Build initial prompt based on personality
        if personality_name == "hybrid_auditor":
            # Include source directory in prompt if specified
            source_info = ""
            if session.config.source_dir:
                source_info = f"\nSource code is available at: {session.config.source_dir}"

            initial_prompt = f"""Begin auditing the application at: {session.target_url}

Your goal: {session.goal}
{source_info}

Exploration approach:
1. First, navigate to the app URL and take a screenshot to understand the UI
2. If source code path is provided, use bash commands to explore it:
   - ls -la {session.config.source_dir or '/path/to/source'} to see files
   - cat <file> to read files
   - find <dir> -name "*.ts" to search for files
3. Look at key files: package.json, README.md, main entry points (app.*, index.*, main.*)
4. Correlate what you see in the UI with what you find in the code
5. Report findings using report_finding for any issues

When navigating to the URL, use waitUntil: "networkidle" to ensure JavaScript has loaded.
"""
        else:
            initial_prompt = f"""Begin testing the application at: {session.target_url}

Your goal: {session.goal}

IMPORTANT: When navigating to any URL, always use waitUntil: "networkidle" to ensure
JavaScript frameworks (React, Next.js, Vue, etc.) have fully hydrated before interacting
with the page. Example: playwright_navigate(url: "...", waitUntil: "networkidle")

Start by navigating to the URL with waitUntil: "networkidle", then take a screenshot
to see the current state. Then proceed according to your personality and testing approach.

Remember to report findings using the report_finding tool as you encounter them.
"""

        action_sequence = 0
        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(initial_prompt)

                async for message in client.receive_messages():
                    # Track actions from tool use
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, ToolUseBlock):
                                if block.name == "report_finding":
                                    # Structured Finding
                                    try:
                                        finding = Finding(
                                            agent_run_id=agent_run.id,
                                            category=FindingCategory(block.input.get("category")),
                                            severity=FindingSeverity(block.input.get("severity")),
                                            title=block.input.get("title"),
                                            description=block.input.get("description"),
                                            action_sequence=[a.sequence for a in agent_run.actions[-5:]],
                                        )
                                        agent_run.findings.append(finding)

                                        # Emit finding event
                                        if event_callback:
                                            await event_callback("finding_reported", {
                                                "personality": personality_name,
                                                "category": finding.category.value,
                                                "severity": finding.severity.value,
                                                "title": finding.title,
                                                "description": finding.description,
                                                "finding_index": len(agent_run.findings) - 1,
                                            })
                                    except Exception as e:
                                        print(f"Error parsing finding: {e}")

                                else:
                                    # Regular browser action
                                    action = self._tool_use_to_action(
                                        block, action_sequence
                                    )
                                    if action:
                                        agent_run.actions.append(action)
                                        action_sequence += 1

                                        # Emit action event
                                        if event_callback:
                                            await event_callback("action_taken", {
                                                "personality": personality_name,
                                                "action_type": action.action_type.value,
                                                "action_sequence": action.sequence,
                                                "parameters": action.parameters,
                                            })

                    # Check for completion
                    if isinstance(message, ResultMessage):
                        if message.is_error:
                            agent_run.fail()
                        else:
                            agent_run.complete()
                        break

                # Interview the agent for a verdict (all personalities)
                if agent_run.status != AgentRunStatus.FAILED:
                    interview_prompt = personality_cls.get_verdict_prompt()
                    await client.query(interview_prompt)
                    
                    verdict_text = ""
                    async for message in client.receive_messages():
                        if isinstance(message, AssistantMessage):
                            for block in message.content:
                                if isinstance(block, TextBlock):
                                    verdict_text += block.text
                        if isinstance(message, ResultMessage):
                            break
                    
                    # Simple parsing of the verdict
                    agent_run.verdict = self._parse_verdict(verdict_text)

        except Exception as e:
            agent_run.fail()
            # Log the error as a finding
            agent_run.findings.append(
                Finding(
                    agent_run_id=agent_run.id,
                    category=FindingCategory.BUG,
                    severity=FindingSeverity.HIGH,
                    title="Agent execution failed",
                    description=str(e),
                    action_sequence=[a.sequence for a in agent_run.actions],
                )
            )
            
        # Calculate score for this run
        agent_run.score = calculate_agent_score(agent_run)

        return agent_run

    def _tool_use_to_action(
        self, tool_use: ToolUseBlock, sequence: int
    ) -> Action | None:
        """Convert a tool use block to an Action model.

        Maps Playwright MCP tool names to our ActionType enum for consistent
        tracking regardless of the underlying automation tool. Returns None
        for unrecognized tools.
        """
        tool_name = tool_use.name
        tool_input = tool_use.input

        # print(f"DEBUG: Processing tool use: {tool_name}")  # Debug logging

        # Special handling for Bash tool from the model
        if tool_name == "Bash":
            command = tool_input.get("command", "") if isinstance(tool_input, dict) else str(tool_input)
            return Action(
                sequence=sequence,
                action_type=ActionType.TYPE,
                parameters={
                    "element": "Terminal",
                    "text": command
                }
            )

        # Map using suffixes for robustness against namespace changes
        suffix_map = {
            "navigate": ActionType.NAVIGATE,
            "click": ActionType.CLICK,
            "fill": ActionType.TYPE,
            "scroll": ActionType.SCROLL,
            "hover": ActionType.HOVER,
            "screenshot": ActionType.SCREENSHOT,
            "press_key": ActionType.PRESS_KEY,
            "select": ActionType.SELECT,
            "wait_for": ActionType.WAIT,
            "snapshot": ActionType.SCREENSHOT,
            "evaluate": ActionType.WAIT,
        }

        action_type = None
        for suffix, type_enum in suffix_map.items():
            if tool_name.endswith(suffix):
                action_type = type_enum
                break

        if action_type is None:
            return None

        return Action(
            sequence=sequence,
            action_type=action_type,
            parameters=dict(tool_input) if isinstance(tool_input, dict) else {},
        )



    def _parse_verdict(self, text: str) -> AgentVerdict:
        """Parse the structured verdict response.

        Expected format:
            FIRST_SCREEN: Yes/No
            OVERRIDES: 0 - none
            COGNITIVE_LOAD: Reduced/Neutral/Increased
            TRUST_SCORE: 1-10
            WOULD_USE_AGAIN: Yes/No

            COMMENTARY:
            [multi-line text]
        """
        import re
        verdict = AgentVerdict()

        # Normalize text for parsing
        text_upper = text.upper()

        # Parse FIRST_SCREEN
        match = re.search(r'FIRST_SCREEN\s*:\s*(YES|NO)', text_upper)
        if match:
            verdict.first_screen_acceptable = match.group(1) == "YES"

        # Parse OVERRIDES - extract count and reason
        match = re.search(r'OVERRIDES\s*:\s*(\d+)(?:\s*[-–—]\s*(.+))?', text, re.IGNORECASE)
        if match:
            verdict.override_count = int(match.group(1))
            if match.group(2):
                verdict.override_reasons.append(match.group(2).strip())

        # Parse COGNITIVE_LOAD
        match = re.search(r'COGNITIVE_LOAD\s*:\s*(REDUCED|NEUTRAL|INCREASED)', text_upper)
        if match:
            load_map = {
                "REDUCED": CognitiveLoad.REDUCED,
                "NEUTRAL": CognitiveLoad.NEUTRAL,
                "INCREASED": CognitiveLoad.INCREASED,
            }
            verdict.cognitive_load = load_map.get(match.group(1), CognitiveLoad.UNKNOWN)

        # Parse TRUST_SCORE
        match = re.search(r'TRUST_SCORE\s*:\s*(\d+)', text_upper)
        if match:
            verdict.trust_level = int(match.group(1))

        # Parse WOULD_USE_AGAIN
        match = re.search(r'WOULD_USE_AGAIN\s*:\s*(YES|NO)', text_upper)
        if match:
            verdict.would_use_again = match.group(1) == "YES"

        # Parse COMMENTARY - everything after "COMMENTARY:" label
        match = re.search(r'COMMENTARY\s*:\s*\n?([\s\S]+)', text, re.IGNORECASE)
        if match:
            verdict.commentary = match.group(1).strip()

        # Fallback: if no structured fields found, treat entire text as commentary
        if (verdict.first_screen_acceptable is None and
            verdict.trust_level == 0 and
            not verdict.commentary):
            verdict.commentary = text.strip() if text.strip() else "No commentary provided"

        return verdict
