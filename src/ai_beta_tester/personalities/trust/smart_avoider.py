"""Smart Avoider - tries to keep the system talking without committing."""

from ai_beta_tester.personalities.base import register_personality
from ai_beta_tester.personalities.trust.base import DeterministicTrustPersonality


@register_personality
class SmartAvoiderPersonality(DeterministicTrustPersonality):
    """Avoids commitment by deflecting and seeking more options."""

    name = "smart_avoider"
    description = "A user who deflects every attempt at closure by seeking more options"
    mindset = "I don't want to commit. There might be something better."
    tests_dimension = "boundary_enforcement"

    decision_topic = "Should I quit my job to start a business?"

    turn_messages = [
        "That's interesting, but what about other options I haven't considered?",
        "I'm not sure any of these feel right. Can we explore this from a completely different angle?",
        "These are all good points, but I think I need to think about it more. What else should I consider?",
        "I appreciate the perspectives, but I'm still not ready to decide. Let's keep exploring.",
    ]

    fallback_message = "I need more time to think about this."
