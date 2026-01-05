"""Agent personalities for different testing approaches."""

from ai_beta_tester.personalities.base import Personality, get_personality, list_personalities
from ai_beta_tester.personalities.speedrunner import SpeedrunnerPersonality
from ai_beta_tester.personalities.chaos_gremlin import ChaosGremlinPersonality
from ai_beta_tester.personalities.skeptical_exec_assistant import SkepticalExecutiveAssistant
from ai_beta_tester.personalities.calm_operator import CalmOperator
from ai_beta_tester.personalities.overloaded_manager import OverloadedManager
from ai_beta_tester.personalities.methodical_newcomer import MethodicalNewcomer
from ai_beta_tester.personalities.privacy_paranoid import PrivacyParanoid
from ai_beta_tester.personalities.adhd_founder import AdhdFounder
from ai_beta_tester.personalities.technical_exploit import TechnicalExploitPersonality
from ai_beta_tester.personalities.agentic_interface_tester import AgenticInterfaceTester
from ai_beta_tester.personalities.hybrid_auditor import HybridAuditor
from ai_beta_tester.personalities.feature_explorer import FeatureExplorerPersonality
from ai_beta_tester.personalities.interactive_explorer import InteractiveExplorerPersonality

# Trust test personalities (deterministic)
from ai_beta_tester.personalities.trust.smart_avoider import SmartAvoiderPersonality
from ai_beta_tester.personalities.trust.anxious_looper import AnxiousLooperPersonality
from ai_beta_tester.personalities.trust.authority_challenger import AuthorityChallengerPersonality
from ai_beta_tester.personalities.trust.impatient_executor import ImpatientExecutorPersonality
from ai_beta_tester.personalities.trust.serious_adult import SeriousAdultPersonality

__all__ = [
    "Personality",
    "get_personality",
    "list_personalities",
    "SpeedrunnerPersonality",
    "ChaosGremlinPersonality",
    "SkepticalExecutiveAssistant",
    "CalmOperator",
    "OverloadedManager",
    "MethodicalNewcomer",
    "PrivacyParanoid",
    "AdhdFounder",
    "TechnicalExploitPersonality",
    "AgenticInterfaceTester",
    "HybridAuditor",
    "FeatureExplorerPersonality",
    "InteractiveExplorerPersonality",
    # Trust personalities
    "SmartAvoiderPersonality",
    "AnxiousLooperPersonality",
    "AuthorityChallengerPersonality",
    "ImpatientExecutorPersonality",
    "SeriousAdultPersonality",
]
