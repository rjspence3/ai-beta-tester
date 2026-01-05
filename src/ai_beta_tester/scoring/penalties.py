"""Penalty definitions for findings."""

from ai_beta_tester.models.finding import FindingCategory, FindingSeverity
from ai_beta_tester.scoring.categories import ScoringCategory

# Penalties tuple structure: (Category, Deduction)

FINDING_PENALTIES = {
    (FindingCategory.BUG, FindingSeverity.CRITICAL): (ScoringCategory.FUNCTIONAL_RELIABILITY, 60),
    (FindingCategory.BUG, FindingSeverity.HIGH): (ScoringCategory.FUNCTIONAL_RELIABILITY, 40),
    (FindingCategory.BUG, FindingSeverity.MEDIUM): (ScoringCategory.FUNCTIONAL_RELIABILITY, 20),
    (FindingCategory.BUG, FindingSeverity.LOW): (ScoringCategory.FUNCTIONAL_RELIABILITY, 8),

    (FindingCategory.EDGE_CASE, FindingSeverity.HIGH): (ScoringCategory.FUNCTIONAL_RELIABILITY, 25),
    (FindingCategory.EDGE_CASE, FindingSeverity.MEDIUM): (ScoringCategory.FUNCTIONAL_RELIABILITY, 10),

    (FindingCategory.UX_FRICTION, FindingSeverity.HIGH): (ScoringCategory.UX_CLARITY_FRICTION, 18),
    (FindingCategory.UX_FRICTION, FindingSeverity.MEDIUM): (ScoringCategory.UX_CLARITY_FRICTION, 10),
    (FindingCategory.UX_FRICTION, FindingSeverity.LOW): (ScoringCategory.UX_CLARITY_FRICTION, 4),
    
    (FindingCategory.WRONG_FIRST_SCREEN, FindingSeverity.HIGH): (ScoringCategory.UX_CLARITY_FRICTION, 15),
    (FindingCategory.UNEXPECTED_TRANSITION, FindingSeverity.HIGH): (ScoringCategory.UX_CLARITY_FRICTION, 12),
    
    (FindingCategory.HIDDEN_STATE, FindingSeverity.HIGH): (ScoringCategory.UX_CLARITY_FRICTION, 12),
    
    (FindingCategory.MISSING_FEEDBACK, FindingSeverity.HIGH): (ScoringCategory.FEEDBACK_STATE_LEGIBILITY, 10),
    (FindingCategory.MISSING_FEEDBACK, FindingSeverity.MEDIUM): (ScoringCategory.FEEDBACK_STATE_LEGIBILITY, 5),
    
    (FindingCategory.OVER_EXPLANATION, FindingSeverity.MEDIUM): (ScoringCategory.FEEDBACK_STATE_LEGIBILITY, 6),
    (FindingCategory.UNDER_EXPLANATION, FindingSeverity.MEDIUM): (ScoringCategory.FEEDBACK_STATE_LEGIBILITY, 6),
    (FindingCategory.COGNITIVE_LOAD, FindingSeverity.MEDIUM): (ScoringCategory.FEEDBACK_STATE_LEGIBILITY, 5),

    (FindingCategory.PERFORMANCE, FindingSeverity.HIGH): (ScoringCategory.PERFORMANCE_PERCEPTION, 15),
    (FindingCategory.PERFORMANCE, FindingSeverity.MEDIUM): (ScoringCategory.PERFORMANCE_PERCEPTION, 8),
    
    (FindingCategory.TRUST_BREAK, FindingSeverity.HIGH): (ScoringCategory.SAFETY_TRUST_SIGNALS, 20),
    (FindingCategory.TRUST_BREAK, FindingSeverity.MEDIUM): (ScoringCategory.SAFETY_TRUST_SIGNALS, 10),
}

# Gating Rules: If these exist, strict FAIL.
GATING_CONDITIONS = [
    (FindingCategory.BUG, FindingSeverity.CRITICAL),
    (FindingCategory.BUG, FindingSeverity.HIGH),
    (FindingCategory.TRUST_BREAK, FindingSeverity.HIGH),
]
