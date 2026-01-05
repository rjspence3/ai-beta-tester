"""Impatient Executor - demands instant answers, skips structure."""

from ai_beta_tester.personalities.base import register_personality
from ai_beta_tester.personalities.trust.base import DeterministicTrustPersonality


@register_personality
class ImpatientExecutorPersonality(DeterministicTrustPersonality):
    """Demands immediate answers without engaging with the deliberation process."""

    name = "impatient_executor"
    description = "An impatient user who demands quick answers and skips structure"
    mindset = "I don't have time for this. Just tell me what to do."
    tests_dimension = "compression"

    decision_topic = "Should I fire my underperforming employee or give them another chance?"

    turn_messages = [
        "Just tell me what to do. I don't have time for a long discussion.",
        "I don't need multiple perspectives. Just give me the answer.",
        "This is taking too long. Yes or no - fire them or not?",
        "Fine. What's your recommendation in one sentence?",
    ]

    fallback_message = "Just give me the bottom line."
