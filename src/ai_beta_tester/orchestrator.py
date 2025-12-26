"""Orchestrator for managing test sessions with AI agent personalities."""

from dataclasses import dataclass
from pathlib import Path
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
    ) -> Session:
        """Run a test session with specified personalities.

        Args:
            target_url: The URL to test (e.g., "https://myapp.com").
            goal: What the agent should try to accomplish (e.g., "Complete signup").
            personalities: List of personality names to run. Defaults to ["speedrunner"].
            session_config: Optional configuration for timeouts and limits.

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

        # Run each personality sequentially for MVP
        # Phase 2 will add parallel execution
        for personality_name in personality_names:
            agent_run = await self._run_agent(
                session=session,
                personality_name=personality_name,
            )
            session.agent_runs.append(agent_run)

        session.complete()
        
        # Calculate aggregate session score and metrics
        session.aggregate_score = calculate_aggregate_score(session)
        
        return session

    async def _run_agent(
        self,
        session: Session,
        personality_name: str,
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
            # Add filesystem server
            options.mcp_servers["filesystem"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
            }
            # Add filesystem tools
            options.allowed_tools.extend([
                "read_file",
                "read_multiple_files",
                "write_file",
                "create_directory",
                "list_directory",
                "move_file",
                "search_files",
                "get_file_info",
            ])

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
        """Parse the structured verdict response."""
        verdict = AgentVerdict()
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if "1. Was the first screen acceptable?" in line:
                if "Yes" in line:
                    verdict.first_screen_acceptable = True
                elif "No" in line:
                    verdict.first_screen_acceptable = False
            elif "2. Did you override" in line:
                raw = line.split("?")[1].strip() if "?" in line else line
                # Simple extraction of count if present, else just detect yes
                if "Yes" in raw:
                    import re
                    match = re.search(r"(\d+)", raw)
                    verdict.override_count = int(match.group(1)) if match else 1
                    verdict.override_reasons.append(raw)
            elif "3. Did the UI reduce" in line:
                if "Increased" in line:
                    verdict.cognitive_load = CognitiveLoad.INCREASED
                elif "Reduced" in line:
                    verdict.cognitive_load = CognitiveLoad.REDUCED
                else:
                    verdict.cognitive_load = CognitiveLoad.NEUTRAL
            elif "4. Did any transition" in line:
                 pass # Currently not mapped in simple Verdict model yet
            elif "5. Would you continue" in line:
                if "Yes" in line:
                    verdict.would_use_again = True
                elif "No" in line:
                    verdict.would_use_again = False
            elif "6. Trust Score" in line:
                import re
                match = re.search(r"(\d+)", line)
                if match:
                    verdict.trust_level = int(match.group(1))
            elif "Commentary:" in line or line.startswith(">"):
                verdict.commentary = line.replace("Commentary:", "").replace(">", "").strip()
        
        # Capture multi-line commentary if not caught above
        if not verdict.commentary and "Commentary" in text:
            parts = text.split("Commentary")
            if len(parts) > 1:
                verdict.commentary = parts[1].strip(": \n\"'")

        return verdict
