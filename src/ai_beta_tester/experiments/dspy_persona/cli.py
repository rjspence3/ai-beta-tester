"""CLI for running persona prompt optimization experiments."""

import asyncio
from pathlib import Path

import typer

from .compare import run_comparison, run_full_comparison, print_report, print_detailed_report
from .dataset import list_personas
from .optimize import get_baseline_prompt, generate_optimized_prompt

app = typer.Typer(
    name="experiment",
    help="Persona prompt optimization experiments",
)


@app.command()
def compare(
    target_url: str = typer.Argument(..., help="URL to test against"),
    persona: str = typer.Option(
        "anxious_looper",
        "--persona", "-p",
        help="Persona to test",
    ),
    runs: int = typer.Option(
        3,
        "--runs", "-n",
        help="Number of runs per variant",
    ),
    output_dir: str = typer.Option(
        None,
        "--output", "-o",
        help="Directory to save results",
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed", "-d",
        help="Show detailed report",
    ),
):
    """Run baseline vs. optimized comparison for a persona."""

    async def _run():
        result = await run_comparison(
            target_url=target_url,
            persona_name=persona,
            num_runs=runs,
        )

        print_report({persona: result})

        if detailed:
            print_detailed_report(result)

        if output_dir:
            import json
            from datetime import datetime

            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = out_path / f"comparison_{persona}_{timestamp}.json"

            with open(file_path, "w") as f:
                json.dump(result.to_dict(), f, indent=2)

            print(f"\nResults saved to: {file_path}")

    asyncio.run(_run())


@app.command()
def compare_all(
    target_url: str = typer.Argument(..., help="URL to test against"),
    runs: int = typer.Option(
        3,
        "--runs", "-n",
        help="Number of runs per variant",
    ),
    output_dir: str = typer.Option(
        "./experiment_results",
        "--output", "-o",
        help="Directory to save results",
    ),
):
    """Run comparison for all personas."""

    async def _run():
        results = await run_full_comparison(
            target_url=target_url,
            num_runs=runs,
            output_dir=Path(output_dir) if output_dir else None,
        )

        print_report(results)

    asyncio.run(_run())


@app.command()
def show_prompts(
    persona: str = typer.Argument(..., help="Persona to show prompts for"),
):
    """Show baseline vs. optimized prompts without running tests."""

    print(f"\n{'='*70}")
    print(f"PROMPT COMPARISON: {persona}")
    print(f"{'='*70}")

    baseline = get_baseline_prompt(persona)
    print(f"\n--- BASELINE PROMPT ({len(baseline)} chars) ---")
    print(baseline)

    print("\nGenerating optimized prompt...")
    optimized = generate_optimized_prompt(persona)
    print(f"\n--- OPTIMIZED PROMPT ({len(optimized)} chars) ---")
    print(optimized)


@app.command()
def list_available():
    """List available personas for testing."""

    personas = list_personas()

    print("\nAvailable personas:")
    for name in personas:
        print(f"  - {name}")


def main():
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
