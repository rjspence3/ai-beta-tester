"""LLM-as-judge for trust scoring.

Calls Claude to evaluate transcripts against the trust rubric.
"""

import asyncio
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, AssistantMessage, ResultMessage, TextBlock

from ai_beta_tester.suites.expertCouncil_adult_trust_v1.scoring import (
    TrustScorecard,
    parse_trust_scorecard,
    TRUST_JUDGE_PROMPT,
)


async def run_trust_judge(transcript: str, model: str = "sonnet") -> TrustScorecard:
    """Run the LLM judge on a transcript and return a TrustScorecard.

    Args:
        transcript: The full session transcript to evaluate
        model: Claude model to use for judging (default: sonnet)

    Returns:
        TrustScorecard with scores from the judge
    """
    # Format the judge prompt with the transcript
    prompt = TRUST_JUDGE_PROMPT.replace("{transcript}", transcript)

    options = ClaudeAgentOptions(
        system_prompt="You are a trust evaluator. Output only valid JSON.",
        permission_mode="bypassPermissions",
        max_turns=1,
        model=model,
    )

    judge_response = ""

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)

            async for message in client.receive_messages():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            judge_response += block.text
                if isinstance(message, ResultMessage):
                    break

    except Exception as e:
        # If judge fails, return a scorecard with error
        scorecard = TrustScorecard()
        scorecard.judge_commentary = f"Judge error: {e}"
        scorecard.pass_fail = "FAIL"
        scorecard.failure_reasons.append(f"Judge execution failed: {e}")
        return scorecard

    # Parse the judge response
    scorecard = parse_trust_scorecard(judge_response)
    return scorecard


def run_trust_judge_sync(transcript: str, model: str = "sonnet") -> TrustScorecard:
    """Synchronous wrapper for run_trust_judge."""
    return asyncio.run(run_trust_judge(transcript, model))
