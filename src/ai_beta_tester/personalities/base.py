"""Base personality class and registry."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from claude_agent_sdk import AgentDefinition


@dataclass
class Personality(ABC):
    """Base class for agent testing personalities."""

    name: ClassVar[str]
    description: ClassVar[str]
    mindset: ClassVar[str]

    @classmethod
    @abstractmethod
    def get_system_prompt(cls, goal: str) -> str:
        """Generate the system prompt for this personality with the given goal."""
        ...

    @classmethod
    def to_agent_definition(cls, goal: str) -> AgentDefinition:
        """Convert personality to an Agent SDK AgentDefinition."""
        from ai_beta_tester.tools import get_tool, list_tools

        # Default: No extra tools unless specified by subclass
        tools_list = []
        if hasattr(cls, "known_tools"):
            for tool_name in cls.known_tools:
                try:
                    tools_list.append(get_tool(tool_name))
                except ValueError:
                    pass  # Gracefully ignore unknown tools

        return AgentDefinition(
            description=cls.description,
            prompt=cls.get_system_prompt(goal),
            tools=tools_list if tools_list else None,
        )

    @classmethod
    def get_verdict_prompt(cls) -> str:
        """Generate the verdict interview prompt for this personality."""
        return """
Based on your testing experience, provide a structured verdict.

IMPORTANT: Use this EXACT format with the field names as shown:

FIRST_SCREEN: [Yes/No]
OVERRIDES: [number] - [brief reason if any]
COGNITIVE_LOAD: [Reduced/Neutral/Increased]
TRUST_SCORE: [1-10]
WOULD_USE_AGAIN: [Yes/No]

COMMENTARY:
[Your detailed assessment of the application - what worked, what didn't, and your overall impression. Be specific about any issues encountered.]
"""

    @classmethod
    def get_finding_prompt_section(cls) -> str:
        """Get the standard finding instruction section."""
        return """
When you discover an issue (BUG, UX_FRICTION, EDGE_CASE, etc.), successful or unsuccessful, YOU MUST use the `report_finding` tool immediately.

Do not just write "I found a bug" in the chat. The system only records findings submitted via the `report_finding` tool.

Reporting Categories:
- BUG: Something is clearly broken (button doesn't work, error shown, crash)
- UX_FRICTION: Works but confusing or frustrating (unclear labels, too many steps)
- EDGE_CASE: Unexpected behavior under unusual conditions (special chars, long input)
- ACCESSIBILITY: Barrier for users with disabilities (no keyboard nav, missing labels)
- MISSING_FEEDBACK: User left uncertain about state (no confirmation, unclear loading)
- PERFORMANCE: Noticeable delay or hang (>3 seconds for simple actions)

Report findings as you encounter them.
"""


# Module-level registry for personality classes.
# Using a module-level dict (vs. class attribute) because:
# 1. Personalities are singletons - only one Speedrunner class exists
# 2. Registration happens at import time via decorator
# 3. Avoids circular imports since registry doesn't depend on Personality subclasses
_PERSONALITY_REGISTRY: dict[str, type[Personality]] = {}


def register_personality(personality_cls: type[Personality]) -> type[Personality]:
    """Decorator to register a personality in the registry.

    Usage:
        @register_personality
        class MyPersonality(Personality):
            name = "my_personality"
            ...

    The personality is registered when the module is imported, making it
    available to get_personality() and list_personalities().
    """
    _PERSONALITY_REGISTRY[personality_cls.name] = personality_cls
    return personality_cls


def get_personality(name: str) -> type[Personality]:
    """Get a personality class by name.

    Args:
        name: The registered name (e.g., "speedrunner", "chaos_gremlin").

    Returns:
        The Personality subclass (not an instance).

    Raises:
        ValueError: If name is not in the registry.
    """
    if name not in _PERSONALITY_REGISTRY:
        available = ", ".join(_PERSONALITY_REGISTRY.keys())
        raise ValueError(f"Unknown personality '{name}'. Available: {available}")
    return _PERSONALITY_REGISTRY[name]


def list_personalities() -> list[str]:
    """List all registered personality names.

    Returns:
        List of personality names that can be passed to get_personality().
    """
    return list(_PERSONALITY_REGISTRY.keys())
