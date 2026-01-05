"""Scoring categories and weights."""

class ScoringCategory:
    FUNCTIONAL_RELIABILITY = "Functional Reliability"
    UX_CLARITY_FRICTION = "UX Clarity & Friction"
    FEEDBACK_STATE_LEGIBILITY = "Feedback & State Legibility"
    ERROR_HANDLING_RECOVERY = "Error Handling & Recovery"
    PERFORMANCE_PERCEPTION = "Performance Perception"
    SAFETY_TRUST_SIGNALS = "Safety & Trust Signals"

CATEGORY_WEIGHTS = {
    ScoringCategory.FUNCTIONAL_RELIABILITY: 25,
    ScoringCategory.UX_CLARITY_FRICTION: 25,
    ScoringCategory.FEEDBACK_STATE_LEGIBILITY: 15,
    ScoringCategory.ERROR_HANDLING_RECOVERY: 15,
    ScoringCategory.PERFORMANCE_PERCEPTION: 10,
    ScoringCategory.SAFETY_TRUST_SIGNALS: 10,
}
