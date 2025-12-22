"""Finding model for tracking discovered issues."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class FindingCategory(Enum):
    """Categories of findings.

    Categories help prioritize fixes and route issues to the right team:
    - BUG: Engineering priority - something is objectively broken
    - UX_FRICTION: Design priority - works but causes user frustration
    - EDGE_CASE: QA priority - unusual inputs reveal unexpected behavior
    - ACCESSIBILITY: Compliance priority - barriers for disabled users
    - MISSING_FEEDBACK: UX priority - user left uncertain about state
    - PERFORMANCE: Infrastructure priority - unacceptable delays
    """

    BUG = "bug"  # Broken functionality: crashes, errors, non-responsive elements
    UX_FRICTION = "ux_friction"  # Confusing or frustrating: unclear labels, excess steps
    EDGE_CASE = "edge_case"  # Unusual input handling: special chars, boundaries
    ACCESSIBILITY = "accessibility"  # Disability barriers: no keyboard nav, missing ARIA
    MISSING_FEEDBACK = "missing_feedback"  # State uncertainty: no confirmation, silent fails
    PERFORMANCE = "performance"  # Slowness: >3s response times, perceived hangs


class FindingSeverity(Enum):
    """Severity levels for findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Finding:
    """An issue discovered during testing."""

    agent_run_id: UUID
    category: FindingCategory
    severity: FindingSeverity
    title: str
    description: str
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.now)
    screenshot_path: str | None = None
    reproduction_steps: list[str] = field(default_factory=list)
    action_sequence: list[int] = field(default_factory=list)

    @property
    def severity_emoji(self) -> str:
        """Get emoji for severity level."""
        match self.severity:
            case FindingSeverity.CRITICAL:
                return "!!"
            case FindingSeverity.HIGH:
                return "!"
            case FindingSeverity.MEDIUM:
                return "-"
            case FindingSeverity.LOW:
                return "."
