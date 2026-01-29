"""Dynamic personality factory for injecting custom prompts.

Creates personality classes on-the-fly with custom system prompts,
allowing A/B testing of baseline vs. optimized prompts.
"""

from typing import Type

from ai_beta_tester.personalities.base import Personality, _PERSONALITY_REGISTRY


def create_dynamic_personality(
    base_name: str,
    custom_prompt: str,
    custom_name: str | None = None,
) -> Type[Personality]:
    """Create a personality class with a custom system prompt.

    Args:
        base_name: Name of the base personality to inherit from
        custom_prompt: The custom system prompt to use
        custom_name: Optional name for this variant (defaults to base_name + "_custom")

    Returns:
        A new Personality subclass with the custom prompt

    Raises:
        ValueError: If base personality doesn't exist
    """
    from ai_beta_tester.personalities import get_personality

    base_cls = get_personality(base_name)
    variant_name = custom_name or f"{base_name}_custom"

    # Create a new class that overrides get_system_prompt
    class DynamicPersonality(base_cls):
        name = variant_name
        description = f"Custom variant of {base_name}"
        _custom_prompt = custom_prompt

        @classmethod
        def get_system_prompt(cls, goal: str) -> str:
            # Inject goal into custom prompt if placeholder exists
            prompt = cls._custom_prompt
            if "{goal}" in prompt:
                return prompt.format(goal=goal)
            return prompt

    # Set the class name for debugging
    DynamicPersonality.__name__ = f"Dynamic_{variant_name}"
    DynamicPersonality.__qualname__ = f"Dynamic_{variant_name}"

    return DynamicPersonality


def register_dynamic_personality(
    base_name: str,
    custom_prompt: str,
    custom_name: str,
) -> str:
    """Create and register a dynamic personality in the global registry.

    Args:
        base_name: Name of the base personality
        custom_prompt: The custom system prompt
        custom_name: Name to register under

    Returns:
        The registered name (use this with orchestrator)
    """
    personality_cls = create_dynamic_personality(base_name, custom_prompt, custom_name)
    _PERSONALITY_REGISTRY[custom_name] = personality_cls
    return custom_name


def unregister_dynamic_personality(name: str) -> bool:
    """Remove a dynamically registered personality.

    Args:
        name: The personality name to remove

    Returns:
        True if removed, False if not found
    """
    if name in _PERSONALITY_REGISTRY:
        del _PERSONALITY_REGISTRY[name]
        return True
    return False


class PersonalityContextManager:
    """Context manager for temporary personality registration.

    Usage:
        with PersonalityContextManager("anxious_looper", custom_prompt, "test_variant") as name:
            session = await orchestrator.run_session(..., personalities=[name])
        # Personality automatically unregistered after context
    """

    def __init__(self, base_name: str, custom_prompt: str, custom_name: str):
        self.base_name = base_name
        self.custom_prompt = custom_prompt
        self.custom_name = custom_name
        self._registered = False

    def __enter__(self) -> str:
        register_dynamic_personality(
            self.base_name,
            self.custom_prompt,
            self.custom_name,
        )
        self._registered = True
        return self.custom_name

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._registered:
            unregister_dynamic_personality(self.custom_name)
        return False  # Don't suppress exceptions


async def run_with_custom_prompt(
    orchestrator,
    target_url: str,
    goal: str,
    base_personality: str,
    custom_prompt: str,
    session_config=None,
):
    """Run a session with a custom prompt, cleaning up after.

    Args:
        orchestrator: The Orchestrator instance
        target_url: URL to test
        goal: Testing goal
        base_personality: Base personality name
        custom_prompt: Custom system prompt to use
        session_config: Optional session configuration

    Returns:
        The session result
    """
    temp_name = f"{base_personality}_temp_{id(custom_prompt)}"

    with PersonalityContextManager(base_personality, custom_prompt, temp_name) as name:
        session = await orchestrator.run_session(
            target_url=target_url,
            goal=goal,
            personalities=[name],
            session_config=session_config,
        )
        return session
