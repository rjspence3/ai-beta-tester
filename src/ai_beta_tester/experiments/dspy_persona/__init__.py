"""Persona prompt optimization experiment.

This experiment tests whether optimized prompts improve
the quality of AI tester agents playing specific personas.

Uses ClaudeSDKClient for all LLM calls (no external API key needed).
"""

from .transcript import ConversationTranscript
from .dataset import list_personas, get_persona_data, PERSONAS
from .judge import score_transcript, FidelityScores
from .compare import run_comparison, print_report, ComparisonResult
from .optimize import get_baseline_prompt, generate_optimized_prompt

__all__ = [
    "run_comparison",
    "print_report",
    "score_transcript",
    "ConversationTranscript",
    "FidelityScores",
    "ComparisonResult",
    "list_personas",
    "get_persona_data",
    "get_baseline_prompt",
    "generate_optimized_prompt",
    "PERSONAS",
]
