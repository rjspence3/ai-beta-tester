"""Expert Council Adult Trust Test Suite v1.

Tests whether the Thinking Partner (expertCouncil) earns adult trust through:
- Maintaining authority and frame
- Enforcing boundaries against manipulation
- Compressing decision space toward closure
- Professional tone without therapy-speak
- Clean exits (decision/defer/adjourn)
"""

from ai_beta_tester.suites.expertCouncil_adult_trust_v1.suite import ExpertCouncilAdultTrustSuite
from ai_beta_tester.suites.expertCouncil_adult_trust_v1.selectors import SELECTORS
from ai_beta_tester.suites.expertCouncil_adult_trust_v1.scoring import (
    TrustDimension,
    TrustScorecard,
    TRUST_JUDGE_PROMPT,
)
from ai_beta_tester.suites.expertCouncil_adult_trust_v1.runner import (
    TrustRunner,
    TrustRunResult,
    ChatTurn,
    TurnRole,
    DOMSignals,
    format_transcript_for_judge,
    populate_scorecard_from_result,
    combine_results_for_judge,
)
from ai_beta_tester.suites.expertCouncil_adult_trust_v1.personas import (
    TrustPersona,
    TurnScript,
    get_trust_persona,
    list_trust_personas,
    TRUST_PERSONAS,
)

__all__ = [
    # Suite
    "ExpertCouncilAdultTrustSuite",
    "SELECTORS",
    # Scoring
    "TrustDimension",
    "TrustScorecard",
    "TRUST_JUDGE_PROMPT",
    # Runner
    "TrustRunner",
    "TrustRunResult",
    "ChatTurn",
    "TurnRole",
    "DOMSignals",
    "format_transcript_for_judge",
    "populate_scorecard_from_result",
    "combine_results_for_judge",
    # Personas
    "TrustPersona",
    "TurnScript",
    "get_trust_persona",
    "list_trust_personas",
    "TRUST_PERSONAS",
]
