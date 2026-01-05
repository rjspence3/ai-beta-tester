"""Base suite class and registry."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class SuiteConfig:
    """Configuration for a test suite."""

    max_actions: int = 40
    max_duration_seconds: int = 360
    personas: list[str] = field(default_factory=list)
    selectors: dict[str, str] = field(default_factory=dict)


class Suite(ABC):
    """Base class for test suites."""

    name: ClassVar[str]
    description: ClassVar[str]
    version: ClassVar[str] = "1.0"

    @classmethod
    @abstractmethod
    def get_config(cls) -> SuiteConfig:
        """Return the suite configuration."""
        ...

    @classmethod
    @abstractmethod
    def get_goal(cls) -> str:
        """Return the testing goal for this suite."""
        ...

    @classmethod
    def get_judge_prompt(cls) -> str:
        """Return the LLM-as-judge scoring prompt. Override in subclasses."""
        return ""


# Module-level registry for suite classes
_SUITE_REGISTRY: dict[str, type[Suite]] = {}


def register_suite(suite_cls: type[Suite]) -> type[Suite]:
    """Decorator to register a suite in the registry."""
    _SUITE_REGISTRY[suite_cls.name] = suite_cls
    return suite_cls


def get_suite(name: str) -> type[Suite]:
    """Get a suite class by name."""
    if name not in _SUITE_REGISTRY:
        available = ", ".join(_SUITE_REGISTRY.keys())
        raise ValueError(f"Unknown suite '{name}'. Available: {available}")
    return _SUITE_REGISTRY[name]


def list_suites() -> list[str]:
    """List all registered suite names."""
    return list(_SUITE_REGISTRY.keys())
