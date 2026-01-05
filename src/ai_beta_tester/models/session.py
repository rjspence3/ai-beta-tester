"""Session model for tracking test runs."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from ai_beta_tester.models.agent_run import AgentRun
    from ai_beta_tester.models.rubric import AggregateRubricScore


class SessionStatus(Enum):
    """Status of a test session."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SessionConfig:
    """Configuration for a test session."""

    max_duration_seconds: int = 300
    max_actions: int = 50
    viewport_width: int = 1280
    viewport_height: int = 720
    source_dir: str | None = None  # Source code directory for hybrid_auditor
    agent_delay_seconds: int = 5  # Delay between agents to avoid API rate limits


@dataclass
class Session:
    """A test session containing one or more agent runs."""

    target_url: str
    goal: str
    id: UUID = field(default_factory=uuid4)
    config: SessionConfig = field(default_factory=SessionConfig)
    status: SessionStatus = field(default=SessionStatus.PENDING)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    agent_runs: list["AgentRun"] = field(default_factory=list)
    aggregate_score: "AggregateRubricScore | None" = field(default=None)

    def start(self) -> None:
        """Mark session as started."""
        self.status = SessionStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self) -> None:
        """Mark session as completed."""
        self.status = SessionStatus.COMPLETED
        self.ended_at = datetime.now()

    def fail(self) -> None:
        """Mark session as failed."""
        self.status = SessionStatus.FAILED
        self.ended_at = datetime.now()

    @property
    def duration_seconds(self) -> float | None:
        """Get session duration in seconds."""
        if self.started_at is None:
            return None
        end = self.ended_at or datetime.now()
        return (end - self.started_at).total_seconds()
