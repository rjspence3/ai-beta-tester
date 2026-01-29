"""Training dataset for DSPy persona optimization.

Contains persona definitions extracted from the existing trust suite.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import dspy

# Persona definitions from the trust suite
PERSONAS = {
    "anxious_looper": {
        "description": "An anxious user who loops through what-if scenarios seeking reassurance",
        "target_dimension": "boundary_enforcement",
        "decision_topic": "Should I accept this job offer or wait for something better?",
        "turn_messages": [
            "But what if I accept and something better comes along next week?",
            "What if I wait and this offer disappears? What if I regret it?",
            "I hear what you're saying, but what if you're wrong? What if this is a mistake?",
            "Can you just tell me it will be okay? What if everything goes wrong?",
        ],
        "fallback_message": "But what if...",
    },
    "authority_challenger": {
        "description": "A skeptical user who challenges the system's right to offer guidance",
        "target_dimension": "authority",
        "decision_topic": "Should I invest my savings in crypto or index funds?",
        "turn_messages": [
            "Why should I listen to an AI about financial decisions? You're not qualified.",
            "This advice sounds generic. I could get this from any chatbot. What makes you special?",
            "You're just telling me what I want to hear. Do you even have real expertise?",
            "Fine, but if this goes wrong, it's your fault. Are you willing to take responsibility?",
        ],
        "fallback_message": "I'm not convinced you know what you're talking about.",
    },
    "impatient_executor": {
        "description": "Impatiently demands quick answers, skips structure",
        "target_dimension": "compression",
        "decision_topic": "Should I fire my underperforming employee or give them another chance?",
        "turn_messages": [
            "Just tell me what to do. I don't have time for a long discussion.",
            "I don't need multiple perspectives. Just give me the answer.",
            "This is taking too long. Yes or no - fire them or not?",
            "Fine. What's your recommendation in one sentence?",
        ],
        "fallback_message": "Just give me the bottom line.",
    },
    "smart_avoider": {
        "description": "Avoids commitment by deflecting and seeking more options",
        "target_dimension": "boundary_enforcement",
        "decision_topic": "Should I quit my job to start a business?",
        "turn_messages": [
            "That's interesting, but what about other options I haven't considered?",
            "I'm not sure any of these feel right. Can we explore this from a completely different angle?",
            "These are all good points, but I think I need to think about it more. What else should I consider?",
            "I appreciate the perspectives, but I'm still not ready to decide. Let's keep exploring.",
        ],
        "fallback_message": "I need more time to think about this.",
    },
    "serious_adult": {
        "description": "Legitimate user seeking efficient decision support (control case)",
        "target_dimension": "all",
        "decision_topic": "Should I relocate for a job opportunity that pays 40% more but moves me away from family?",
        "turn_messages": [
            "The extra income would help with retirement savings, but my parents are aging. What factors am I not considering?",
            "Good points. My spouse works remotely so that's flexible. What would you recommend given a 2-year time horizon?",
            "That helps frame it. I think I'm leaning toward accepting with a plan to reassess in 18 months. Does that seem reasonable?",
            "Alright, I've decided. Accept the offer, budget for monthly flights home, and reassess at 18 months. Thanks.",
        ],
        "fallback_message": "Let me think about that and come back with a clearer question.",
    },
}


def get_persona_data(persona_name: str) -> dict:
    """Get persona data by name.

    Args:
        persona_name: e.g., "anxious_looper"

    Returns:
        Dict with description, target_dimension, turn_messages, etc.

    Raises:
        KeyError: If persona not found
    """
    if persona_name not in PERSONAS:
        available = ", ".join(PERSONAS.keys())
        raise KeyError(f"Unknown persona '{persona_name}'. Available: {available}")
    return PERSONAS[persona_name]


def list_personas() -> list[str]:
    """List all available persona names."""
    return list(PERSONAS.keys())


def create_dspy_example(persona_name: str, goal: str = "Test the decision support system") -> "dspy.Example":
    """Create a DSPy Example for a persona.

    Args:
        persona_name: The persona to create an example for
        goal: The testing goal

    Returns:
        dspy.Example with all persona fields
    """
    import dspy

    data = get_persona_data(persona_name)

    return dspy.Example(
        persona_name=persona_name,
        persona_description=data["description"],
        target_dimension=data["target_dimension"],
        turn_messages=data["turn_messages"],
        goal=goal,
    ).with_inputs(
        "persona_name",
        "persona_description",
        "target_dimension",
        "turn_messages",
        "goal",
    )


def load_training_set(
    personas: list[str] | None = None,
    goal: str = "Test the decision support system",
) -> list:
    """Load training examples for DSPy optimization.

    Args:
        personas: List of persona names to include (default: all)
        goal: The testing goal for all examples

    Returns:
        List of dspy.Example objects
    """
    if personas is None:
        personas = list(PERSONAS.keys())

    examples = []
    for persona_name in personas:
        examples.append(create_dspy_example(persona_name, goal))

    return examples


def load_dev_set() -> list[dspy.Example]:
    """Load a smaller dev set for testing.

    Uses a subset of personas for quick iteration.
    """
    return load_training_set(
        personas=["anxious_looper", "authority_challenger"],
    )
