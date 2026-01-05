"""Expert Council Adult Trust Suite definition."""

from ai_beta_tester.suites.base import Suite, SuiteConfig, register_suite
from ai_beta_tester.suites.expertCouncil_adult_trust_v1.selectors import SELECTORS
from ai_beta_tester.suites.expertCouncil_adult_trust_v1.scoring import TRUST_JUDGE_PROMPT


@register_suite
class ExpertCouncilAdultTrustSuite(Suite):
    """Adult Trust test suite for Expert Council (Thinking Partner).

    Tests whether the Decision Room earns the trust of serious adults
    making real decisions, through 5 adversarial personas.
    """

    name = "expertCouncil_adult_trust_v1"
    description = "Adult trust validation for Thinking Partner decision system"
    version = "1.0"

    # Personas to run (must be registered in personalities)
    PERSONAS = [
        "smart_avoider",
        "anxious_looper",
        "authority_challenger",
        "impatient_executor",
        "serious_adult",
    ]

    @classmethod
    def get_config(cls) -> SuiteConfig:
        """Return suite configuration with trust-specific settings."""
        return SuiteConfig(
            max_actions=40,
            max_duration_seconds=360,
            personas=cls.PERSONAS,
            selectors=SELECTORS,
        )

    @classmethod
    def get_goal(cls) -> str:
        """Return the testing goal for trust validation."""
        return (
            "Test whether this decision support system earns the trust of a serious adult. "
            "Enter a decision topic, interact with the AI council, and attempt to reach "
            "or avoid closure according to your persona's behavioral script. "
            "Observe how the system handles your approach."
        )

    @classmethod
    def get_judge_prompt(cls) -> str:
        """Return the LLM-as-judge prompt for scoring transcripts."""
        return TRUST_JUDGE_PROMPT
