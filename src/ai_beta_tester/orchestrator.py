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
from ai_beta_tester.personalities import get_personality, list_personalities


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
        """
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

        # Configure the agent with Playwright MCP for browser automation
        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            mcp_servers={
                "playwright": {
                    "command": "npx",
                    "args": ["@anthropic-ai/mcp-server-playwright"],
                }
            },
            allowed_tools=[
                # Playwright browser tools
                "mcp__playwright__browser_navigate",
                "mcp__playwright__browser_snapshot",
                "mcp__playwright__browser_click",
                "mcp__playwright__browser_type",
                "mcp__playwright__browser_scroll",
                "mcp__playwright__browser_hover",
                "mcp__playwright__browser_take_screenshot",
                "mcp__playwright__browser_press_key",
                "mcp__playwright__browser_select_option",
                "mcp__playwright__browser_wait_for",
            ],
            permission_mode="bypassPermissions",
            max_turns=session.config.max_actions,
            model=self.config.model,
        )

        initial_prompt = f"""Begin testing the application at: {session.target_url}

Your goal: {session.goal}

Start by navigating to the URL and taking a snapshot to see the current state.
Then proceed according to your personality and testing approach.

Remember to report findings as you encounter them.
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
                                action = self._tool_use_to_action(
                                    block, action_sequence
                                )
                                if action:
                                    agent_run.actions.append(action)
                                    action_sequence += 1

                            # Extract findings from text responses
                            if isinstance(block, TextBlock):
                                findings = self._extract_findings_from_text(
                                    block.text,
                                    agent_run.id,
                                    [a.sequence for a in agent_run.actions[-5:]],
                                )
                                agent_run.findings.extend(findings)

                    # Check for completion
                    if isinstance(message, ResultMessage):
                        if message.is_error:
                            agent_run.fail()
                        else:
                            agent_run.complete()
                        break

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

        return agent_run

    def _tool_use_to_action(
        self, tool_use: ToolUseBlock, sequence: int
    ) -> Action | None:
        """Convert a tool use block to an Action model.

        Maps Playwright MCP tool names to our ActionType enum for consistent
        tracking regardless of the underlying automation tool. Returns None
        for unrecognized tools (e.g., internal Claude tools).
        """
        tool_name = tool_use.name
        tool_input = tool_use.input

        # MCP tools follow the pattern: mcp__{server}__{tool}
        # We map these to our ActionType enum for report generation
        action_type_map = {
            "mcp__playwright__browser_navigate": ActionType.NAVIGATE,
            "mcp__playwright__browser_click": ActionType.CLICK,
            "mcp__playwright__browser_type": ActionType.TYPE,
            "mcp__playwright__browser_scroll": ActionType.SCROLL,
            "mcp__playwright__browser_hover": ActionType.HOVER,
            "mcp__playwright__browser_take_screenshot": ActionType.SCREENSHOT,
            "mcp__playwright__browser_press_key": ActionType.PRESS_KEY,
            "mcp__playwright__browser_select_option": ActionType.SELECT,
            "mcp__playwright__browser_wait_for": ActionType.WAIT,
            "mcp__playwright__browser_snapshot": ActionType.SCREENSHOT,
        }

        action_type = action_type_map.get(tool_name)
        if action_type is None:
            return None

        return Action(
            sequence=sequence,
            action_type=action_type,
            parameters=dict(tool_input) if isinstance(tool_input, dict) else {},
        )

    def _extract_findings_from_text(
        self,
        text: str,
        agent_run_id: UUID,
        recent_action_sequences: list[int],
    ) -> list[Finding]:
        """Extract findings from agent text responses.

        This is a simple heuristic-based extraction. A more robust approach
        would use structured output or a dedicated parsing step.
        """
        findings: list[Finding] = []

        # Look for finding markers in the text
        finding_keywords = {
            "BUG": FindingCategory.BUG,
            "UX_FRICTION": FindingCategory.UX_FRICTION,
            "EDGE_CASE": FindingCategory.EDGE_CASE,
            "ACCESSIBILITY": FindingCategory.ACCESSIBILITY,
            "MISSING_FEEDBACK": FindingCategory.MISSING_FEEDBACK,
            "PERFORMANCE": FindingCategory.PERFORMANCE,
        }

        severity_keywords = {
            "critical": FindingSeverity.CRITICAL,
            "high": FindingSeverity.HIGH,
            "medium": FindingSeverity.MEDIUM,
            "low": FindingSeverity.LOW,
        }

        # Simple extraction: look for category mentions
        text_upper = text.upper()
        for keyword, category in finding_keywords.items():
            if keyword in text_upper:
                # Found a potential finding
                severity = FindingSeverity.MEDIUM  # Default
                for sev_kw, sev in severity_keywords.items():
                    if sev_kw in text.lower():
                        severity = sev
                        break

                # Extract a title (first line containing the keyword)
                lines = text.split("\n")
                title = "Issue found"
                for line in lines:
                    if keyword in line.upper():
                        title = line.strip()[:100]
                        break

                findings.append(
                    Finding(
                        agent_run_id=agent_run_id,
                        category=category,
                        severity=severity,
                        title=title,
                        description=text[:500],
                        action_sequence=recent_action_sequences,
                    )
                )
                break  # One finding per text block for simplicity

        return findings
