"""Agent run model for tracking individual personality test runs."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from ai_beta_tester.models.action import Action
    from ai_beta_tester.models.finding import Finding
    from ai_beta_tester.models.rubric import AgentVerdict, RubricScore


class AgentRunStatus(Enum):
    """Status of an agent run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    STUCK = "stuck"
    FAILED = "failed"


@dataclass
class AgentRun:
    """A single agent personality's test run within a session."""

    session_id: UUID
    personality: str
    id: UUID = field(default_factory=uuid4)
    status: AgentRunStatus = field(default=AgentRunStatus.PENDING)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    actions: list["Action"] = field(default_factory=list)
    findings: list["Finding"] = field(default_factory=list)
    verdict: "AgentVerdict | None" = field(default=None)
    score: "RubricScore | None" = field(default=None)

    def start(self) -> None:
        """Mark agent run as started."""
        self.status = AgentRunStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self) -> None:
        """Mark agent run as completed."""
        self.status = AgentRunStatus.COMPLETED
        self.ended_at = datetime.now()

    def mark_stuck(self) -> None:
        """Mark agent run as stuck."""
        self.status = AgentRunStatus.STUCK
        self.ended_at = datetime.now()

    def fail(self) -> None:
        """Mark agent run as failed."""
        self.status = AgentRunStatus.FAILED
        self.ended_at = datetime.now()

    @property
    def duration_seconds(self) -> float | None:
        """Get agent run duration in seconds."""
        if self.started_at is None:
            return None
        end = self.ended_at or datetime.now()
        return (end - self.started_at).total_seconds()

    @property
    def action_count(self) -> int:
        """Get number of actions taken."""
        return len(self.actions)

    @property
    def finding_count(self) -> int:
        """Get number of findings."""
        return len(self.findings)
