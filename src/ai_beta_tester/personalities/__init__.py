"""Agent personalities for different testing approaches."""

from ai_beta_tester.personalities.base import Personality, get_personality, list_personalities
from ai_beta_tester.personalities.speedrunner import SpeedrunnerPersonality
from ai_beta_tester.personalities.chaos_gremlin import ChaosGremlinPersonality

__all__ = [
    "Personality",
    "get_personality",
    "list_personalities",
    "SpeedrunnerPersonality",
    "ChaosGremlinPersonality",
]
