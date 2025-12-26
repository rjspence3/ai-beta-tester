import pytest
from unittest.mock import AsyncMock, patch
from ai_beta_tester.orchestrator import Orchestrator, OrchestratorConfig
from ai_beta_tester.models import Session, AgentRun

@pytest.mark.asyncio
async def test_run_session_initialization():
    """Test that run_session initializes a session correctly."""
    orch = Orchestrator()
    
    with patch.object(orch, '_run_agent', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = AgentRun(session_id=1, personality="speedrunner")
        
        session = await orch.run_session(
            target_url="https://example.com",
            goal="Test Goal",
            personalities=["speedrunner"]
        )
        
        assert session.target_url == "https://example.com"
        assert session.goal == "Test Goal"
        assert len(session.agent_runs) == 1
        assert session.agent_runs[0].personality == "speedrunner"

@pytest.mark.asyncio
async def test_invalid_personality():
    """Test that unknown personalities raise ValueError."""
    orch = Orchestrator()
    
    with pytest.raises(ValueError, match="Unknown personality"):
        await orch.run_session(
            target_url="https://example.com",
            goal="Test",
            personalities=["invalid_persona"]
        )

@pytest.mark.skip(reason="localhost blocking disabled for local dev")
@pytest.mark.asyncio
async def test_security_violation_propagation():
    """Test that blocked URLs raise SecurityViolation."""
    from ai_beta_tester.security import SecurityViolation
    orch = Orchestrator()
    
    # Mocking NavigationGuard logic if we wanted, but we rely on the real one here 
    # as it's a fast unit test.
    with pytest.raises(SecurityViolation):
        await orch.run_session(
            target_url="http://localhost:8080",
            goal="Test"
        )
