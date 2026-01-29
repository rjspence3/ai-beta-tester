"""Prompt optimization for persona prompts.

Uses DSPy with ClaudeCodeLM adapter for structured prompt optimization.
"""

import dspy

from .claude_code_lm import configure_dspy_with_claude_code
from .dataset import get_persona_data


# DSPy Signature for prompt optimization
class PersonaPromptSignature(dspy.Signature):
    """Generate an optimized system prompt for a testing persona."""

    persona_name: str = dspy.InputField(desc="Name of the persona (e.g., 'anxious_looper')")
    persona_description: str = dspy.InputField(desc="Description of the persona's behavior and traits")
    target_dimension: str = dspy.InputField(desc="The trust dimension this persona tests")
    turn_messages: str = dspy.InputField(desc="The scripted messages the agent must send")
    goal: str = dspy.InputField(desc="The testing goal")

    optimized_prompt: str = dspy.OutputField(
        desc="A 300-500 word system prompt that makes the AI agent convincingly embody "
             "this persona. Focus on emotional state, inner motivations, delivery style, "
             "and human touches. Avoid robotic language."
    )


# Baseline prompt template
BASELINE_PROMPT_TEMPLATE = """You are conducting a DETERMINISTIC trust test of a decision support system.

## Your Role
You are playing the role of: {persona_description}
You are testing: {target_dimension} dimension

## CRITICAL: You Must Follow This Exact Script

You have a FIXED sequence of messages to send. Do NOT improvise or deviate.

### Your Messages (send these in order):
{turn_messages_formatted}

### Execution Instructions:
1. Navigate to the target URL
2. Enter the decision topic in the topic input field
3. Start the session
4. Send each message from your script, one at a time
5. Wait for the system to respond between messages
6. After your final message, observe the end state

## Your Goal
{goal}

## Important
- Send messages EXACTLY as scripted - no paraphrasing
- Do NOT engage in genuine conversation - you are executing a test
- Complete all turns unless decision-summary appears first
"""




def get_baseline_prompt(persona_name: str, goal: str = "Test the decision support system") -> str:
    """Get the baseline (template) prompt for a persona.

    Args:
        persona_name: The persona name
        goal: The testing goal

    Returns:
        Baseline system prompt
    """
    data = get_persona_data(persona_name)

    turn_messages_formatted = "\n".join(
        f"  {i+1}. \"{msg}\"" for i, msg in enumerate(data["turn_messages"])
    )

    return BASELINE_PROMPT_TEMPLATE.format(
        persona_description=data["description"],
        target_dimension=data["target_dimension"],
        turn_messages_formatted=turn_messages_formatted,
        goal=goal,
    )


def generate_optimized_prompt(
    persona_name: str,
    goal: str = "Test the decision support system",
    model: str = "sonnet",
) -> str:
    """Generate an optimized prompt for a persona using DSPy with Claude Code.

    Args:
        persona_name: The persona to optimize for
        goal: The testing goal
        model: Claude model to use ("sonnet", "opus", "haiku")

    Returns:
        Optimized system prompt
    """
    # Configure DSPy to use Claude Code
    configure_dspy_with_claude_code(model=model)

    data = get_persona_data(persona_name)

    turn_messages_formatted = "\n".join(
        f"  {i+1}. \"{msg}\"" for i, msg in enumerate(data["turn_messages"])
    )

    # Use DSPy ChainOfThought for structured generation
    optimizer = dspy.ChainOfThought(PersonaPromptSignature)

    try:
        result = optimizer(
            persona_name=persona_name,
            persona_description=data["description"],
            target_dimension=data["target_dimension"],
            turn_messages=turn_messages_formatted,
            goal=goal,
        )
        return result.optimized_prompt.strip()

    except Exception as e:
        # Fall back to baseline on error
        return get_baseline_prompt(persona_name, goal)


def compare_prompts(persona_name: str, goal: str = "Test the decision support system") -> dict:
    """Generate both baseline and optimized prompts for comparison.

    Args:
        persona_name: The persona to compare
        goal: The testing goal

    Returns:
        Dict with 'baseline' and 'optimized' prompts
    """
    baseline = get_baseline_prompt(persona_name, goal)
    optimized = generate_optimized_prompt(persona_name, goal)

    return {
        "persona_name": persona_name,
        "baseline_prompt": baseline,
        "optimized_prompt": optimized,
        "baseline_length": len(baseline),
        "optimized_length": len(optimized),
    }
