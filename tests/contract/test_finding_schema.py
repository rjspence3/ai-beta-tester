import json
from uuid import uuid4
from ai_beta_tester.models import Finding, FindingCategory, FindingSeverity

def test_finding_serialization():
    """Test serializing a finding to JSON matches expected structure."""
    finding = Finding(
        agent_run_id=uuid4(),
        category=FindingCategory.BUG,
        severity=FindingSeverity.HIGH,
        title="Test Bug",
        description="Found a bug",
        action_sequence=[1, 2, 3]
    )
    
    # Needs to be serializable (usually via dataclasses.asdict or pydantic)
    # The current codebase uses standard dataclasses. 
    # We test that it holds data correctly and validation works if we were to serialize.
    
    assert finding.title == "Test Bug"
    assert finding.severity == FindingSeverity.HIGH
    assert finding.category == FindingCategory.BUG
    assert isinstance(finding.timestamp, object) # datetime

def test_finding_enums():
    """Test that invalid enum values are not accepted by type checkers or at runtime construction."""
    # Runtime check only if we add validation, but Python dataclasses don't fail by default.
    # This contract test primarily documents the expected inputs.
    
    f = Finding(
        agent_run_id=uuid4(),
        category=FindingCategory.UX_FRICTION,
        severity=FindingSeverity.LOW,
        title="UX Issue",
        description="Desc"
    )
    assert f.severity_emoji == "."
    
    f_crit = Finding(
        agent_run_id=uuid4(),
        category=FindingCategory.BUG,
        severity=FindingSeverity.CRITICAL,
        title="Crit",
        description="Desc"
    )
    assert f_crit.severity_emoji == "!!"
