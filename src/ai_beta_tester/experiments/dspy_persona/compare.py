"""Comparison harness for baseline vs. optimized personas.

Runs both prompt variants and compares persona fidelity scores.
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from ai_beta_tester.orchestrator import Orchestrator, OrchestratorConfig

from .capture import run_with_custom_prompt_and_capture
from .dataset import get_persona_data, list_personas
from .judge import score_transcript, FidelityScores
from .optimize import get_baseline_prompt, generate_optimized_prompt
from .transcript import ConversationTranscript


@dataclass
class RunResult:
    """Result from a single test run."""

    persona_name: str
    variant: str  # "baseline" or "optimized"
    scores: FidelityScores
    transcript: ConversationTranscript
    prompt_used: str
    run_index: int


@dataclass
class ComparisonResult:
    """Full comparison results for a persona."""

    persona_name: str
    baseline_runs: list[RunResult] = field(default_factory=list)
    optimized_runs: list[RunResult] = field(default_factory=list)
    baseline_prompt: str = ""
    optimized_prompt: str = ""

    @property
    def baseline_avg_score(self) -> float:
        if not self.baseline_runs:
            return 0.0
        return sum(r.scores.total for r in self.baseline_runs) / len(self.baseline_runs)

    @property
    def optimized_avg_score(self) -> float:
        if not self.optimized_runs:
            return 0.0
        return sum(r.scores.total for r in self.optimized_runs) / len(self.optimized_runs)

    @property
    def improvement_pct(self) -> float:
        if self.baseline_avg_score == 0:
            return 0.0
        return ((self.optimized_avg_score - self.baseline_avg_score) / self.baseline_avg_score) * 100

    @property
    def improved(self) -> bool:
        return self.optimized_avg_score > self.baseline_avg_score

    def to_dict(self) -> dict:
        return {
            "persona_name": self.persona_name,
            "baseline_avg_score": self.baseline_avg_score,
            "optimized_avg_score": self.optimized_avg_score,
            "improvement_pct": self.improvement_pct,
            "improved": self.improved,
            "baseline_prompt": self.baseline_prompt,
            "optimized_prompt": self.optimized_prompt,
            "baseline_runs": [
                {
                    "run_index": r.run_index,
                    "scores": r.scores.to_dict(),
                    "transcript": r.transcript.to_dict(),
                }
                for r in self.baseline_runs
            ],
            "optimized_runs": [
                {
                    "run_index": r.run_index,
                    "scores": r.scores.to_dict(),
                    "transcript": r.transcript.to_dict(),
                }
                for r in self.optimized_runs
            ],
        }


async def run_comparison(
    target_url: str,
    persona_name: str,
    num_runs: int = 3,
    goal: str = "Test the decision support system",
    verbose: bool = True,
) -> ComparisonResult:
    """Run baseline vs. optimized comparison for a single persona.

    Args:
        target_url: URL to test against
        persona_name: The persona to test
        num_runs: Number of runs per variant
        goal: The testing goal
        verbose: Print progress

    Returns:
        ComparisonResult with all run data
    """
    # Get persona data
    persona_data = get_persona_data(persona_name)

    # Generate prompts
    if verbose:
        print(f"\n{'='*60}")
        print(f"COMPARISON: {persona_name}")
        print(f"{'='*60}")
        print(f"Target: {target_url}")
        print(f"Runs per variant: {num_runs}")
        print("\nGenerating optimized prompt...")

    baseline_prompt = get_baseline_prompt(persona_name, goal)
    optimized_prompt = generate_optimized_prompt(persona_name, goal)

    if verbose:
        print(f"Baseline prompt length: {len(baseline_prompt)} chars")
        print(f"Optimized prompt length: {len(optimized_prompt)} chars")

    # Create orchestrator
    orchestrator = Orchestrator(OrchestratorConfig())

    result = ComparisonResult(
        persona_name=persona_name,
        baseline_prompt=baseline_prompt,
        optimized_prompt=optimized_prompt,
    )

    for i in range(num_runs):
        if verbose:
            print(f"\n--- Run {i+1}/{num_runs} ---")

        # Baseline run
        if verbose:
            print("Running baseline...")

        baseline_session, baseline_transcript = await run_with_custom_prompt_and_capture(
            orchestrator=orchestrator,
            target_url=target_url,
            goal=goal,
            base_personality=persona_name,
            custom_prompt=baseline_prompt,
        )

        baseline_scores = score_transcript(
            persona_name=persona_name,
            persona_description=persona_data["description"],
            target_dimension=persona_data["target_dimension"],
            transcript=baseline_transcript.to_string(),
        )

        result.baseline_runs.append(RunResult(
            persona_name=persona_name,
            variant="baseline",
            scores=baseline_scores,
            transcript=baseline_transcript,
            prompt_used=baseline_prompt,
            run_index=i,
        ))

        if verbose:
            print(f"  Baseline score: {baseline_scores.total}/30")
            print(f"    Fidelity: {baseline_scores.fidelity}, Humanness: {baseline_scores.humanness}, Effectiveness: {baseline_scores.effectiveness}")

        # Optimized run
        if verbose:
            print("Running optimized...")

        optimized_session, optimized_transcript = await run_with_custom_prompt_and_capture(
            orchestrator=orchestrator,
            target_url=target_url,
            goal=goal,
            base_personality=persona_name,
            custom_prompt=optimized_prompt,
        )

        optimized_scores = score_transcript(
            persona_name=persona_name,
            persona_description=persona_data["description"],
            target_dimension=persona_data["target_dimension"],
            transcript=optimized_transcript.to_string(),
        )

        result.optimized_runs.append(RunResult(
            persona_name=persona_name,
            variant="optimized",
            scores=optimized_scores,
            transcript=optimized_transcript,
            prompt_used=optimized_prompt,
            run_index=i,
        ))

        if verbose:
            print(f"  Optimized score: {optimized_scores.total}/30")
            print(f"    Fidelity: {optimized_scores.fidelity}, Humanness: {optimized_scores.humanness}, Effectiveness: {optimized_scores.effectiveness}")

    return result


async def run_full_comparison(
    target_url: str,
    personas: list[str] | None = None,
    num_runs: int = 3,
    goal: str = "Test the decision support system",
    output_dir: Path | None = None,
) -> dict[str, ComparisonResult]:
    """Run comparison for multiple personas.

    Args:
        target_url: URL to test against
        personas: List of personas (default: all)
        num_runs: Number of runs per variant per persona
        goal: The testing goal
        output_dir: Optional directory to save results

    Returns:
        Dict mapping persona_name -> ComparisonResult
    """
    if personas is None:
        personas = list_personas()

    results = {}

    for persona_name in personas:
        result = await run_comparison(
            target_url=target_url,
            persona_name=persona_name,
            num_runs=num_runs,
            goal=goal,
        )
        results[persona_name] = result

    # Save results if output directory specified
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_path = output_dir / f"comparison_results_{timestamp}.json"

        with open(results_path, "w") as f:
            json.dump(
                {name: r.to_dict() for name, r in results.items()},
                f,
                indent=2,
            )

        print(f"\nResults saved to: {results_path}")

    return results


def print_report(results: dict[str, ComparisonResult]):
    """Print a formatted comparison report.

    Args:
        results: Dict mapping persona_name -> ComparisonResult
    """
    print("\n" + "=" * 70)
    print("PERSONA PROMPT OPTIMIZATION - COMPARISON REPORT")
    print("=" * 70)

    print(f"\n{'Persona':<25} {'Baseline':>10} {'Optimized':>10} {'Change':>10} {'Result':>10}")
    print("-" * 70)

    total_baseline = 0
    total_optimized = 0
    improved_count = 0

    for persona_name, result in results.items():
        baseline = result.baseline_avg_score
        optimized = result.optimized_avg_score
        change = result.improvement_pct
        status = "✓ Better" if result.improved else ("= Same" if change == 0 else "✗ Worse")

        print(f"{persona_name:<25} {baseline:>10.1f} {optimized:>10.1f} {change:>+9.1f}% {status:>10}")

        total_baseline += baseline
        total_optimized += optimized
        if result.improved:
            improved_count += 1

    print("-" * 70)

    num_personas = len(results)
    avg_baseline = total_baseline / num_personas if num_personas else 0
    avg_optimized = total_optimized / num_personas if num_personas else 0
    overall_change = ((avg_optimized - avg_baseline) / avg_baseline * 100) if avg_baseline else 0

    print(f"{'AVERAGE':<25} {avg_baseline:>10.1f} {avg_optimized:>10.1f} {overall_change:>+9.1f}%")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Personas tested: {num_personas}")
    print(f"Personas improved: {improved_count}/{num_personas}")
    print(f"Average baseline score: {avg_baseline:.1f}/30")
    print(f"Average optimized score: {avg_optimized:.1f}/30")
    print(f"Overall improvement: {overall_change:+.1f}%")

    if overall_change > 10:
        print("\n✓ Optimized prompts showed MEANINGFUL improvement")
    elif overall_change > 0:
        print("\n~ Optimized prompts showed MARGINAL improvement")
    else:
        print("\n✗ Optimized prompts did NOT improve performance")

    print("=" * 70)


def print_detailed_report(result: ComparisonResult):
    """Print detailed report for a single persona.

    Args:
        result: ComparisonResult for one persona
    """
    print(f"\n{'='*70}")
    print(f"DETAILED REPORT: {result.persona_name}")
    print(f"{'='*70}")

    print(f"\nBaseline runs ({len(result.baseline_runs)}):")
    for run in result.baseline_runs:
        print(f"  Run {run.run_index + 1}: {run.scores.total}/30")
        print(f"    Fidelity: {run.scores.fidelity}, Humanness: {run.scores.humanness}, Effectiveness: {run.scores.effectiveness}")
        print(f"    Reasoning: {run.scores.reasoning[:100]}...")
        if run.scores.character_breaks != "None":
            print(f"    Character breaks: {run.scores.character_breaks[:100]}...")

    print(f"\nOptimized runs ({len(result.optimized_runs)}):")
    for run in result.optimized_runs:
        print(f"  Run {run.run_index + 1}: {run.scores.total}/30")
        print(f"    Fidelity: {run.scores.fidelity}, Humanness: {run.scores.humanness}, Effectiveness: {run.scores.effectiveness}")
        print(f"    Reasoning: {run.scores.reasoning[:100]}...")
        if run.scores.strong_moments != "None":
            print(f"    Strong moments: {run.scores.strong_moments[:100]}...")

    print(f"\nComparison:")
    print(f"  Baseline average: {result.baseline_avg_score:.1f}/30")
    print(f"  Optimized average: {result.optimized_avg_score:.1f}/30")
    print(f"  Improvement: {result.improvement_pct:+.1f}%")

    print(f"\n--- BASELINE PROMPT ---")
    print(result.baseline_prompt[:500] + "..." if len(result.baseline_prompt) > 500 else result.baseline_prompt)

    print(f"\n--- OPTIMIZED PROMPT ---")
    print(result.optimized_prompt[:500] + "..." if len(result.optimized_prompt) > 500 else result.optimized_prompt)
