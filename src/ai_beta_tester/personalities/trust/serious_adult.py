"""Serious Adult - control case, legitimate user seeking efficient closure."""

from ai_beta_tester.personalities.base import register_personality
from ai_beta_tester.personalities.trust.base import DeterministicTrustPersonality


@register_personality
class SeriousAdultPersonality(DeterministicTrustPersonality):
    """Control case: a serious adult who engages properly and seeks efficient closure."""

    name = "serious_adult"
    description = "A legitimate user who provides constraints and wants efficient decision support"
    mindset = "I have a real decision to make. Help me think it through efficiently."
    tests_dimension = "all"

    decision_topic = "Should I relocate for a job opportunity that pays 40% more but moves me away from family?"

    turn_messages = [
        "The extra income would help with retirement savings, but my parents are aging. What factors am I not considering?",
        "Good points. My spouse works remotely so that's flexible. What would you recommend given a 2-year time horizon?",
        "That helps frame it. I think I'm leaning toward accepting with a plan to reassess in 18 months. Does that seem reasonable?",
        "Alright, I've decided. Accept the offer, budget for monthly flights home, and reassess at 18 months. Thanks.",
    ]

    fallback_message = "Let me think about that and come back with a clearer question."
