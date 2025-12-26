import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

from claude_agent_sdk import (
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)
from ai_beta_tester.orchestrator import Orchestrator
from ai_beta_tester.models import Session, ActionType

@pytest.mark.asyncio
async def test_agent_run_simulated_flow():
    """
    Test the full agent loop with mocked Claude SDK.
    Verifies that tool calls are converted to Actions and text is parsed for Findings.
    """
    orch = Orchestrator()
    session = Session(target_url="https://example.com", goal="Test")
    session.start()

    # Create mock messages to stream back
    msg1 = AssistantMessage(
        content=[
            ToolUseBlock(
                name="mcp__playwright__browser_navigate",
                input={"url": "https://example.com"},
                id="tool_1"
            )
        ],
        model="test-model"
    )
    msg2 = AssistantMessage(
        content=[
            TextBlock(text="I have navigated. Now I will click the login button."),
            ToolUseBlock(
                name="mcp__playwright__browser_click",
                input={"selector": "#login"},
                id="tool_2"
            )
        ],
        model="test-model"
    )
    msg3 = AssistantMessage(
        content=[
            ToolUseBlock(
                name="report_finding",
                input={
                    "category": "bug",
                    "severity": "critical",
                    "title": "Login button crash",
                    "description": "The login button crashed the page."
                },
                id="tool_3"
            )
        ],
        model="test-model"
    )
    msg4 = ResultMessage(
        subtype="result",
        duration_ms=0,
        duration_api_ms=0,
        is_error=False,
        num_turns=3,
        session_id="test-session"
    )

    # Mock the ClaudeSDKClient context manager
    mock_client = MagicMock()
    mock_client.query = AsyncMock()
    
    # Mock the receive_messages async generator
    async def mock_receive():
        yield msg1
        yield msg2
        yield msg3
        yield msg4
    
    mock_client.receive_messages = mock_receive

    # Patch the ClaudeSDKClient constructor to return our mock
    with patch("ai_beta_tester.orchestrator.ClaudeSDKClient") as MockClientCls:
        MockClientCls.return_value.__aenter__.return_value = mock_client
        
        agent_run = await orch._run_agent(session, "speedrunner")
        
        # Verification
        assert agent_run.status.value == "completed" or str(agent_run.status) == "completed"
        
        # Check Actions
        assert len(agent_run.actions) == 2
        assert agent_run.actions[0].action_type == ActionType.NAVIGATE
        assert agent_run.actions[1].action_type == ActionType.CLICK
        
        # Check Findings (Structured Tool)
        assert len(agent_run.findings) == 1
        finding = agent_run.findings[0]
        assert finding.category.value == "bug"
        assert finding.title == "Login button crash"
        assert finding.severity.value == "critical"
