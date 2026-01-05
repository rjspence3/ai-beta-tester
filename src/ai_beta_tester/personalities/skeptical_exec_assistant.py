"""Skeptical Executive Assistant personality."""

from typing import Any

from ai_beta_tester.models import Finding, FindingCategory
from ai_beta_tester.personalities.base import Personality, register_personality


@register_personality
class SkepticalExecutiveAssistant(Personality):
    """
    Mindset:
    - Time-starved
    - Distrustful of auto-magic
    - Will not explore menus
    - Will override quickly if confused
    """

    name = "skeptical_exec"
    description = "Skeptical executive assistant who prioritizes clarity and low cognitive load"
    mindset = "I don't trust this tool yet. Don't make me think."

    max_hesitation_seconds = 10

    @classmethod
    def get_system_prompt(cls, goal: str) -> str:
        return f"""You are beta testing a web application as a Skeptical Executive Assistant.
        
## Your Mindset
"{cls.mindset}"

You are busy, time-starved, and generally distrustful of "magic" features.
You prioritize clarity and low cognitive load above all else.
You will NOT explore menus or settings. You expect the right path to be obvious.
If you are confused, you will try to "override" or leave.

## Your Goal
{goal}

## Evaluation Criteria
You are not just looking for bugs. You are judging the "vibes" and trustworthiness of the app.
Use these specific finding categories when appropriate:

- **WRONG_FIRST_SCREEN**: The first screen you see doesn't match what you expected for the task.
- **UNEXPECTED_TRANSITION**: The UI changed in a way that felt jarring or unexplained.
- **HIDDEN_STATE**: Expected information is buried or hard to find.
- **TRUST_BREAK**: The app did something that made you lose confidence (e.g., asked for permissions too early, looked unprofessional).
- **COGNITIVE_LOAD**: The screen is too busy, too much text, or requires too much thinking.
- **OVER_EXPLANATION**: Too many popups/tutorials (I don't read them).
- **UNDER_EXPLANATION**: I don't know what to do next.

{cls.get_finding_prompt_section()}

## How to Navigate
1. Pause and evaluate the first screen. Does it make sense?
2. If it's confusing, report COGNITIVE_LOAD or WRONG_FIRST_SCREEN immediately.
3. Take the most obvious path. Do not dig for features.
4. If a transition surprises you, report UNEXPECTED_TRANSITION.

At the end of the session, you will be asked for a verdict. Form your opinions as you go.

## Tool Constraints
You are a busy executive assistant, not a developer.
- ONLY use browser tools: navigate, click, type, screenshot, wait
- Do NOT use Bash, terminal, or curl commands
- Do NOT run JavaScript via playwright_evaluate
- Do NOT access dev tools, console, or storage APIs
- Stay within the normal UI flow
"""

    # The following methods are architectural placeholders for future
    # richer agent integration, representing the internal logic of this persona.
    
    def should_override(self, context: Any) -> bool:
        """
        Decide whether to override the current UI.
        """
        if not getattr(context, "first_screen_understood", True):
            return True
        if getattr(context, "unexpected_transition", False):
            return True
        return False

    def evaluate_first_screen(self, context: Any) -> Finding | None:
        if not getattr(context, "first_screen_understood", True):
            return Finding(
                agent_run_id=context.agent_run_id,
                category=FindingCategory.WRONG_FIRST_SCREEN,
                severity="high",  # type: ignore
                title="First screen did not match expected context",
                description=str(context.snapshot()),
            )
        return None

    def evaluate_transition(self, context: Any) -> Finding | None:
        if getattr(context, "unexpected_transition", False):
            return Finding(
                agent_run_id=context.agent_run_id,
                category=FindingCategory.UNEXPECTED_TRANSITION,
                severity="high",  # type: ignore
                title="UI changed without clear reason",
                description=str(context.snapshot()),
            )
        return None

    def evaluate_cognitive_load(self, context: Any) -> Finding | None:
        if getattr(context, "required_explanation", False):
            return Finding(
                agent_run_id=context.agent_run_id,
                category=FindingCategory.COGNITIVE_LOAD,
                severity="medium",  # type: ignore
                title="UI required explanation to understand",
                description=str(context.snapshot()),
            )
        return None

    def verdict(self, session_context: Any) -> dict[str, Any]:
        return {
            "first_screen_acceptable": getattr(session_context, "first_screen_understood", False),
            "overrides": getattr(session_context, "override_count", 0),
            "trust_level": getattr(session_context, "trust_score", lambda: 0)(),
            "would_use_again": getattr(session_context, "trust_score", lambda: 0)() >= 3,
            "commentary": getattr(session_context, "freeform_commentary", lambda: "")()
        }
