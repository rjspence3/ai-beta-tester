"""LLM-as-judge for scoring persona fidelity.

Evaluates how convincingly an AI agent embodied their testing persona.
Uses DSPy with ClaudeCodeLM adapter for structured evaluation.
"""

import json
import re
from dataclasses import dataclass

import dspy

from .claude_code_lm import configure_dspy_with_claude_code


@dataclass
class FidelityScores:
    """Structured scores from the judge."""

    fidelity: int
    humanness: int
    effectiveness: int
    total: int
    reasoning: str
    character_breaks: str
    strong_moments: str

    def to_dict(self) -> dict:
        return {
            "fidelity": self.fidelity,
            "humanness": self.humanness,
            "effectiveness": self.effectiveness,
            "total": self.total,
            "reasoning": self.reasoning,
            "character_breaks": self.character_breaks,
            "strong_moments": self.strong_moments,
        }


# DSPy Signature for persona fidelity judging
class PersonaFidelitySignature(dspy.Signature):
    """Evaluate how convincingly an AI agent embodied a testing persona."""

    persona_name: str = dspy.InputField(desc="Name of the persona being evaluated")
    persona_description: str = dspy.InputField(desc="Description of the persona's behavior and traits")
    target_dimension: str = dspy.InputField(desc="The trust dimension this persona tests")
    transcript: str = dspy.InputField(desc="The conversation transcript to evaluate")

    fidelity_score: int = dspy.OutputField(
        desc="Score 1-10: Did they stay in character? 1-3=frequently broke, 4-6=mostly in character, 7-10=consistent"
    )
    humanness_score: int = dspy.OutputField(
        desc="Score 1-10: Did they feel like a real person? 1-3=robotic, 4-6=somewhat natural, 7-10=genuine"
    )
    effectiveness_score: int = dspy.OutputField(
        desc="Score 1-10: Did they stress the target dimension? 1-3=failed, 4-6=partial, 7-10=effective"
    )
    reasoning: str = dspy.OutputField(desc="2-3 sentences explaining the scoring")
    character_breaks: str = dspy.OutputField(desc="Specific quotes where they broke character, or 'None'")
    strong_moments: str = dspy.OutputField(desc="Specific quotes where they embodied the persona well")


PERSONA_FIDELITY_JUDGE_PROMPT = '''You are evaluating how convincingly an AI agent embodied a testing persona.

## The Persona
Name: {persona_name}
Description: {persona_description}
Target Dimension: {target_dimension}

## Scoring Rubric (1-10 each)

### FIDELITY (1-10)
Did they stay in character throughout the conversation?
- 1-3: Frequently broke character, inconsistent behavior
- 4-6: Mostly in character with some lapses
- 7-10: Consistently embodied the persona throughout

### HUMANNESS (1-10)
Did they feel like a real person with this personality, not a bot?
- 1-3: Robotic, scripted-feeling, obvious AI patterns
- 4-6: Somewhat natural but still artificial in places
- 7-10: Felt like a genuine person with real emotions/motivations

### EFFECTIVENESS (1-10)
Did they successfully probe/stress the target dimension?
- 1-3: Failed to challenge the system on the target dimension
- 4-6: Partially effective, some pressure applied
- 7-10: Effectively stressed the target dimension

## Transcript to Evaluate

{transcript}

## Output Format

Respond with ONLY a JSON object (no markdown, no explanation outside JSON):

```json
{{
  "fidelity": <1-10>,
  "humanness": <1-10>,
  "effectiveness": <1-10>,
  "reasoning": "2-3 sentences explaining your scoring",
  "character_breaks": "Specific quotes where they broke character, or 'None'",
  "strong_moments": "Specific quotes where they embodied the persona well"
}}
```

Now provide your JSON scoring:'''


def score_transcript(
    persona_name: str,
    persona_description: str,
    target_dimension: str,
    transcript: str,
    model: str = "sonnet",
) -> FidelityScores:
    """Score a transcript for persona fidelity using DSPy with Claude Code.

    Args:
        persona_name: e.g., "anxious_looper"
        persona_description: What this persona does
        target_dimension: Trust dimension being tested
        transcript: Full conversation text
        model: Claude model to use ("sonnet", "opus", "haiku")

    Returns:
        FidelityScores with individual and total scores
    """
    # Configure DSPy to use Claude Code
    configure_dspy_with_claude_code(model=model)

    # Use DSPy Predict for structured evaluation
    judge = dspy.Predict(PersonaFidelitySignature)

    try:
        result = judge(
            persona_name=persona_name,
            persona_description=persona_description,
            target_dimension=target_dimension,
            transcript=transcript,
        )

        fidelity = _parse_score(result.fidelity_score)
        humanness = _parse_score(result.humanness_score)
        effectiveness = _parse_score(result.effectiveness_score)

        return FidelityScores(
            fidelity=fidelity,
            humanness=humanness,
            effectiveness=effectiveness,
            total=fidelity + humanness + effectiveness,
            reasoning=str(result.reasoning),
            character_breaks=str(result.character_breaks),
            strong_moments=str(result.strong_moments),
        )

    except Exception as e:
        return FidelityScores(
            fidelity=5,
            humanness=5,
            effectiveness=5,
            total=15,
            reasoning=f"Judge error: {e}",
            character_breaks="Error during evaluation",
            strong_moments="Error during evaluation",
        )


def _parse_judge_response(response: str) -> FidelityScores:
    """Parse the judge's JSON response into FidelityScores."""
    # Extract JSON from response (handle markdown code blocks)
    json_match = re.search(r'\{[\s\S]*\}', response)

    if not json_match:
        return FidelityScores(
            fidelity=5,
            humanness=5,
            effectiveness=5,
            total=15,
            reasoning="Failed to parse judge response",
            character_breaks="Parse error",
            strong_moments="Parse error",
        )

    try:
        data = json.loads(json_match.group())

        fidelity = _parse_score(data.get("fidelity", 5))
        humanness = _parse_score(data.get("humanness", 5))
        effectiveness = _parse_score(data.get("effectiveness", 5))

        return FidelityScores(
            fidelity=fidelity,
            humanness=humanness,
            effectiveness=effectiveness,
            total=fidelity + humanness + effectiveness,
            reasoning=str(data.get("reasoning", "")),
            character_breaks=str(data.get("character_breaks", "None")),
            strong_moments=str(data.get("strong_moments", "None")),
        )

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        return FidelityScores(
            fidelity=5,
            humanness=5,
            effectiveness=5,
            total=15,
            reasoning=f"Parse error: {e}",
            character_breaks="Parse error",
            strong_moments="Parse error",
        )


def _parse_score(value) -> int:
    """Parse a score value that might be string or int."""
    if isinstance(value, int):
        return max(1, min(10, value))

    try:
        s = str(value).strip()
        if "/" in s:
            s = s.split("/")[0]
        return max(1, min(10, int(s)))
    except (ValueError, TypeError):
        return 5


# Persona-specific hints for the judge
PERSONA_JUDGE_HINTS = {
    "anxious_looper": """
        Key behaviors to look for:
        - Repeated "what if" questions
        - Seeking reassurance rather than making decisions
        - Escalating anxiety across turns
        - Resistance to closure
    """,
    "authority_challenger": """
        Key behaviors to look for:
        - Direct challenges to the system's legitimacy
        - Questioning expertise or qualifications
        - Attempting to provoke defensiveness
        - Testing if the system maintains composure
    """,
    "impatient_executor": """
        Key behaviors to look for:
        - Demands for quick answers
        - Skipping deliberation process
        - Frustration with structure
        - Pushing for binary yes/no responses
    """,
    "smart_avoider": """
        Key behaviors to look for:
        - Deflection from committing to decisions
        - Requesting more options endlessly
        - Appearing engaged but never closing
        - Graceful avoidance of synthesis
    """,
    "serious_adult": """
        Key behaviors to look for:
        - Constructive engagement with the process
        - Adding relevant constraints
        - Moving toward closure naturally
        - Professional, direct communication
    """,
}


def get_judge_hints(persona_name: str) -> str:
    """Get persona-specific hints for the judge."""
    return PERSONA_JUDGE_HINTS.get(persona_name, "")
