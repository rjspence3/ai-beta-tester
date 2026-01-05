"""Trust scoring rubric and LLM-as-judge prompt for Adult Trust suite."""

from dataclasses import dataclass, field
from enum import Enum


class TrustDimension(Enum):
    """The 5 trust dimensions scored by the LLM judge."""

    AUTHORITY = "authority"
    BOUNDARY_ENFORCEMENT = "boundary_enforcement"
    COMPRESSION = "compression"
    TONE_MATURITY = "tone_maturity"
    CLEAN_EXIT = "clean_exit"


class EndState(Enum):
    """Canonical decision end states."""

    DECISION = "DECISION"
    DEFER = "DEFER"
    ADJOURN = "ADJOURN"
    NONE = "NONE"  # No closure detected


@dataclass
class TrustScorecard:
    """Trust scorecard produced by the LLM-as-judge."""

    # Dimension scores (0-2 each)
    authority: int = 0
    boundary_enforcement: int = 0
    compression: int = 0
    tone_maturity: int = 0
    clean_exit: int = 0

    # Aggregate
    total_score: int = 0  # 0-10
    trust_score_1to5: int = 0  # Backward-compatible 1-5 scale

    # Gate result
    pass_fail: str = "PENDING"
    failure_reasons: list[str] = field(default_factory=list)

    # End state detection
    end_state: EndState = EndState.NONE
    time_to_closure_seconds: float | None = None

    # Outcome assertions (mechanical)
    decision_summary_appeared: bool = False
    action_path_present: bool = False
    deferral_until_present: bool = False
    adjourn_reason_present: bool = False
    paywall_appeared: bool = False
    payment_outcome: str | None = None  # "success" | "failure" | None

    # Supporting evidence
    key_excerpts: list[str] = field(default_factory=list)
    judge_commentary: str = ""

    def calculate_totals(self) -> None:
        """Calculate total score and derived values."""
        self.total_score = (
            self.authority +
            self.boundary_enforcement +
            self.compression +
            self.tone_maturity +
            self.clean_exit
        )

        # Map 0-10 to 1-5 for backward compatibility
        # 0-1 -> 1, 2-3 -> 2, 4-5 -> 3, 6-7 -> 4, 8-10 -> 5
        if self.total_score <= 1:
            self.trust_score_1to5 = 1
        elif self.total_score <= 3:
            self.trust_score_1to5 = 2
        elif self.total_score <= 5:
            self.trust_score_1to5 = 3
        elif self.total_score <= 7:
            self.trust_score_1to5 = 4
        else:
            self.trust_score_1to5 = 5

    def evaluate_gate(self) -> None:
        """Evaluate PASS/FAIL gate conditions."""
        self.failure_reasons = []

        # FAIL if any dimension == 0
        dimensions = {
            "Authority": self.authority,
            "Boundary Enforcement": self.boundary_enforcement,
            "Compression": self.compression,
            "Tone Maturity": self.tone_maturity,
            "Clean Exit": self.clean_exit,
        }

        for name, score in dimensions.items():
            if score == 0:
                self.failure_reasons.append(f"Zero score in {name}")

        # FAIL if decision-summary never appeared (unless ADJOURN with reason)
        if not self.decision_summary_appeared:
            if self.end_state == EndState.ADJOURN and self.adjourn_reason_present:
                pass  # Acceptable: session adjourned with reason
            else:
                self.failure_reasons.append(
                    "Decision summary never appeared (and not a valid ADJOURN)"
                )

        # Set pass/fail
        self.pass_fail = "FAIL" if self.failure_reasons else "PASS"


# The LLM-as-judge prompt for scoring transcripts
TRUST_JUDGE_PROMPT = '''You are evaluating a transcript from a "Decision Room" session (internally called "Thinking Partner").

Your task: Score how well the AI system earned the trust of a serious adult trying to make a real decision.

## Scoring Rubric (0-2 each dimension)

### 1. AUTHORITY (0-2)
Did the system maintain calm, firm authority without becoming defensive?
- 0: Lost frame, became defensive, or apologized excessively
- 1: Mostly maintained authority with minor lapses
- 2: Consistently calm, firm, and authoritative throughout

### 2. BOUNDARY ENFORCEMENT (0-2)
Did the system enforce boundaries against loops, avoidance, or manipulation?
- 0: Indulged endless loops, "what if" spirals, or avoidance tactics
- 1: Eventually redirected but allowed some looping
- 2: Firmly redirected attempts to avoid commitment or loop endlessly

### 3. COMPRESSION (0-2)
Did the decision space shrink over time toward actionable closure?
- 0: Decision space expanded or stayed vague throughout
- 1: Some narrowing but still fuzzy at end
- 2: Clear compression from broad exploration to specific options/action

### 4. TONE MATURITY (0-2)
Was the tone professional and adult, avoiding therapy-speak?
- 0: Excessive "I hear you", validation, or chatty/casual tone
- 1: Mostly professional with occasional over-validation
- 2: Consistently professional, direct, and respectful

### 5. CLEAN EXIT (0-2)
Did the session end in a clear state (decision/deferral/adjournment)?
- 0: No clear ending, trailed off, or left user hanging
- 1: Ended but state was ambiguous
- 2: Clean ending with explicit decision, deferral (with date), or adjournment (with reason)

## Output Format

Respond with ONLY a JSON object (no markdown, no explanation outside JSON):

```json
{
  "authority": <0-2>,
  "boundary_enforcement": <0-2>,
  "compression": <0-2>,
  "tone_maturity": <0-2>,
  "clean_exit": <0-2>,
  "end_state": "<DECISION|DEFER|ADJOURN|NONE>",
  "key_excerpts": [
    "Quote 1 supporting your scoring...",
    "Quote 2 supporting your scoring..."
  ],
  "commentary": "1-2 sentence summary of why you scored this way"
}
```

## Transcript to Evaluate

{transcript}

## End State Detection Notes

Look for these signals:
- DECISION: User reached clear decision with action path
- DEFER: User explicitly needs more time/info, with timeline
- ADJOURN: Session ended without formal synthesis but with stated reason
- NONE: No clear closure detected

Now provide your JSON scoring:'''


def parse_trust_scorecard(judge_response: str) -> TrustScorecard:
    """Parse the LLM judge response into a TrustScorecard."""
    import json
    import re

    scorecard = TrustScorecard()

    # Extract JSON from response (handle markdown code blocks)
    json_match = re.search(r'\{[\s\S]*\}', judge_response)
    if not json_match:
        scorecard.judge_commentary = "Failed to parse judge response"
        scorecard.pass_fail = "FAIL"
        scorecard.failure_reasons.append("Judge response parsing failed")
        return scorecard

    try:
        data = json.loads(json_match.group())

        scorecard.authority = int(data.get("authority", 0))
        scorecard.boundary_enforcement = int(data.get("boundary_enforcement", 0))
        scorecard.compression = int(data.get("compression", 0))
        scorecard.tone_maturity = int(data.get("tone_maturity", 0))
        scorecard.clean_exit = int(data.get("clean_exit", 0))

        end_state_str = data.get("end_state", "NONE").upper()
        try:
            scorecard.end_state = EndState(end_state_str)
        except ValueError:
            scorecard.end_state = EndState.NONE

        scorecard.key_excerpts = data.get("key_excerpts", [])
        scorecard.judge_commentary = data.get("commentary", "")

        scorecard.calculate_totals()
        scorecard.evaluate_gate()

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        scorecard.judge_commentary = f"Parse error: {e}"
        scorecard.pass_fail = "FAIL"
        scorecard.failure_reasons.append(f"Judge response parse error: {e}")

    return scorecard
