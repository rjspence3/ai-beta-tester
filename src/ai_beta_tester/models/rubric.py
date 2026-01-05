"""Rubric and scoring models."""

from dataclasses import dataclass, field
from enum import Enum


class CognitiveLoad(Enum):
    """Cognitive load assessment."""
    
    REDUCED = "reduced"
    NEUTRAL = "neutral"
    INCREASED = "increased"
    UNKNOWN = "unknown"


@dataclass
class AgentVerdict:
    """Structured verdict from an agent personality."""
    
    first_screen_acceptable: bool | None = None
    override_count: int = 0
    override_reasons: list[str] = field(default_factory=list)
    cognitive_load: CognitiveLoad = CognitiveLoad.UNKNOWN
    trust_level: int = 0  # 1-10
    would_use_again: bool | None = None
    commentary: str = ""


@dataclass
class RubricScore:
    """Score for a single agent run."""
    
    overall_score: int = 0  # 0-100
    category_scores: dict[str, int] = field(default_factory=dict)  # Category -> Score (0-100)
    pass_fail: str = "PASS"  # "PASS" or "FAIL"
    gating_failures: list[str] = field(default_factory=list)
    top_risks: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    score_version: str = "v1.0"


@dataclass
class AggregateRubricScore:
    """Aggregated score for the entire session."""
    
    overall_score: int = 0  # 0-100
    category_scores: dict[str, int] = field(default_factory=dict)
    pass_fail: str = "PASS"
    gating_failures: list[str] = field(default_factory=list)
    agent_scores: dict[str, RubricScore] = field(default_factory=dict)  # Personality -> Score
    agent_verdicts: dict[str, AgentVerdict] = field(default_factory=dict)  # Personality -> Verdict
    notes: list[str] = field(default_factory=list)
