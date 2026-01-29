"""Command-line interface for AI Beta Tester."""

import asyncio
import atexit
import os
import signal
import subprocess
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ai_beta_tester.models import SessionConfig
from ai_beta_tester.orchestrator import Orchestrator, OrchestratorConfig
from ai_beta_tester.personalities import list_personalities
from ai_beta_tester.reporting import MarkdownReporter
from ai_beta_tester.suites import get_suite, list_suites

app = typer.Typer(
    name="ai-beta-test",
    help="AI-powered exploratory testing with distinct agent personalities",
    no_args_is_help=True,
)

# Add experiment subcommand
from ai_beta_tester.experiments.dspy_persona.cli import app as experiment_app
app.add_typer(experiment_app, name="experiment", help="Persona prompt optimization experiments")
console = Console()


def _cleanup_playwright_browsers() -> None:
    """Kill any orphaned Playwright browser processes spawned by this tool."""
    try:
        # Find Playwright Chromium processes
        result = subprocess.run(
            ["pgrep", "-f", "ms-playwright/chromium"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                except (ProcessLookupError, ValueError):
                    pass
    except Exception:
        pass  # Best effort cleanup


def _signal_handler(signum: int, frame) -> None:
    """Handle interrupt signals by cleaning up browsers."""
    _cleanup_playwright_browsers()
    raise SystemExit(130)  # Standard exit code for SIGINT


# Register cleanup handlers
atexit.register(_cleanup_playwright_browsers)
signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


@app.command()
def run(
    url: Annotated[str, typer.Argument(help="Target URL to test")],
    goal: Annotated[
        str, typer.Option("--goal", "-g", help="Goal for the test session")
    ] = "Explore the application and find issues",
    agents: Annotated[
        str | None,
        typer.Option(
            "--agents",
            "-a",
            help="Comma-separated list of agent personalities to run",
        ),
    ] = None,
    max_actions: Annotated[
        int, typer.Option("--max-actions", help="Maximum actions per agent")
    ] = 50,
    max_duration: Annotated[
        int, typer.Option("--max-duration", help="Maximum duration in seconds")
    ] = 300,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output directory for reports"),
    ] = None,
    source_dir: Annotated[
        str | None,
        typer.Option("--source-dir", "-s", help="Source code directory for hybrid_auditor to read"),
    ] = None,
    agent_delay: Annotated[
        int,
        typer.Option("--agent-delay", help="Delay in seconds between agents to avoid API rate limits"),
    ] = 5,
) -> None:
    """Run a test session against a target URL."""
    # Parse agent list
    personality_names: list[str] | None = None
    if agents:
        personality_names = [a.strip() for a in agents.split(",")]

    # Validate personalities
    available = list_personalities()
    if personality_names:
        for name in personality_names:
            if name not in available:
                console.print(
                    f"[red]Unknown personality '{name}'[/red]\n"
                    f"Available: {', '.join(available)}"
                )
                raise typer.Exit(1)
    else:
        personality_names = ["speedrunner"]  # Default

    # Configure session
    session_config = SessionConfig(
        max_actions=max_actions,
        max_duration_seconds=max_duration,
        source_dir=source_dir,
        agent_delay_seconds=agent_delay,
    )

    orchestrator_config = OrchestratorConfig()
    if output:
        orchestrator_config.sessions_dir = output / "sessions"
        orchestrator_config.screenshots_dir = output / "screenshots"

    # Show session info
    console.print(
        Panel(
            f"[bold]Target:[/bold] {url}\n"
            f"[bold]Goal:[/bold] {goal}\n"
            f"[bold]Agents:[/bold] {', '.join(personality_names)}\n"
            f"[bold]Max Actions:[/bold] {max_actions}\n"
            f"[bold]Max Duration:[/bold] {max_duration}s",
            title="[bold blue]AI Beta Test Session[/bold blue]",
        )
    )

    # Run the session
    orchestrator = Orchestrator(orchestrator_config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running test session...", total=None)

        try:
            session = asyncio.run(
                orchestrator.run_session(
                    target_url=url,
                    goal=goal,
                    personalities=personality_names,
                    session_config=session_config,
                )
            )
        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted. Cleaning up...[/yellow]")
            _cleanup_playwright_browsers()
            raise typer.Exit(130)
        except Exception as e:
            console.print(f"[red]Session failed: {e}[/red]")
            _cleanup_playwright_browsers()
            raise typer.Exit(1)

        progress.update(task, description="Generating report...")

    # Generate report
    reporter = MarkdownReporter(output_dir=output or Path("./reports"))
    report_path = reporter.save(session)

    # Show results summary
    console.print()

    # Results table
    table = Table(title="Results Summary")
    table.add_column("Personality", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Actions", justify="right")
    table.add_column("Findings", justify="right", style="yellow")

    for run in session.agent_runs:
        status_style = (
            "green"
            if run.status.value == "completed"
            else "yellow"
            if run.status.value == "stuck"
            else "red"
        )
        table.add_row(
            run.personality.replace("_", " ").title(),
            f"[{status_style}]{run.status.value.title()}[/{status_style}]",
            str(run.action_count),
            str(run.finding_count),
        )

    console.print(table)

    # Findings summary
    total_findings = sum(run.finding_count for run in session.agent_runs)
    if total_findings > 0:
        console.print(f"\n[yellow]Found {total_findings} issue(s)[/yellow]")
    else:
        console.print("\n[green]No issues found[/green]")

    console.print(f"\n[dim]Report saved to: {report_path}[/dim]")


@app.command()
def personalities() -> None:
    """List available agent personalities."""
    available = list_personalities()

    table = Table(title="Available Personalities")
    table.add_column("Name", style="cyan")
    table.add_column("Description")

    from ai_beta_tester.personalities import get_personality

    for name in available:
        personality = get_personality(name)
        table.add_row(name, personality.description)

    console.print(table)


@app.command()
def report(
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Path to session data"),
    ] = None,
    latest: Annotated[
        bool, typer.Option("--latest", "-l", help="Show the latest report")
    ] = False,
) -> None:
    """View test reports."""
    reports_dir = Path("./reports")

    if not reports_dir.exists():
        console.print("[yellow]No reports found. Run a test session first.[/yellow]")
        raise typer.Exit(1)

    if latest:
        # Find the most recent report
        reports = sorted(reports_dir.glob("*.md"), key=lambda p: p.stat().st_mtime)
        if not reports:
            console.print("[yellow]No reports found.[/yellow]")
            raise typer.Exit(1)

        path = reports[-1]

    if path and path.exists():
        content = path.read_text()
        console.print(content)
    else:
        # List available reports
        reports = sorted(reports_dir.glob("*.md"), key=lambda p: p.stat().st_mtime)
        if not reports:
            console.print("[yellow]No reports found.[/yellow]")
            raise typer.Exit(1)

        table = Table(title="Available Reports")
        table.add_column("Filename", style="cyan")
        table.add_column("Modified")

        for report_file in reports:
            from datetime import datetime

            mtime = datetime.fromtimestamp(report_file.stat().st_mtime)
            table.add_row(report_file.name, mtime.strftime("%Y-%m-%d %H:%M"))

        console.print(table)
        console.print("\n[dim]Use --path to view a specific report[/dim]")


async def _run_trust_suite(
    url: str,
    suite_cls: type,
    persona_names: list[str],
    progress_callback: callable = None,
    headless: bool = True,
    auth_token: str | None = None,
) -> tuple[list, "TrustScorecard"]:
    """Run trust suite with deterministic TrustRunner.

    Args:
        url: Target URL to test
        suite_cls: The suite class (e.g., ExpertCouncilAdultTrustSuite)
        persona_names: List of persona names to run
        progress_callback: Optional callback for progress updates
        headless: Whether to run browser in headless mode
        auth_token: Optional JWT token for authentication

    Returns:
        Tuple of (list of TrustRunResult, TrustScorecard)
    """
    from urllib.parse import urlparse
    from playwright.async_api import async_playwright

    from ai_beta_tester.suites.expertCouncil_adult_trust_v1.runner import (
        TrustRunner,
        TrustRunResult,
        format_transcript_for_judge,
        populate_scorecard_from_result,
        combine_results_for_judge,
    )
    from ai_beta_tester.suites.expertCouncil_adult_trust_v1.personas import get_trust_persona
    from ai_beta_tester.suites.expertCouncil_adult_trust_v1.scoring import TrustScorecard
    from ai_beta_tester.suites.expertCouncil_adult_trust_v1.judge import run_trust_judge

    suite_config = suite_cls.get_config()
    results: list[TrustRunResult] = []

    # Extract domain for cookie
    parsed_url = urlparse(url)
    domain = parsed_url.hostname or "localhost"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)

        # Create context with auth cookie if token provided
        context = await browser.new_context()
        if auth_token:
            await context.add_cookies([{
                "name": "session",
                "value": auth_token,
                "domain": domain,
                "path": "/",
            }])

        for i, persona_name in enumerate(persona_names):
            if progress_callback:
                progress_callback(f"Running {persona_name.replace('_', ' ').title()} ({i+1}/{len(persona_names)})...")

            # Create fresh page for each persona (shares auth context)
            page = await context.new_page()

            try:
                # Navigate to target
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Get persona and run
                persona = get_trust_persona(persona_name)
                runner = TrustRunner(
                    selectors=suite_config.selectors,
                    timeout_seconds=suite_config.max_duration_seconds,
                )

                result = await runner.run_persona(page, persona)
                results.append(result)

            except Exception as e:
                # Record failed run
                results.append(TrustRunResult(
                    persona_name=persona_name,
                    decision_topic="",
                    stop_reason="error",
                    error=str(e),
                ))

            finally:
                await page.close()

        await browser.close()

    # Build combined transcript for judge
    if progress_callback:
        progress_callback("Running LLM judge...")

    transcript = combine_results_for_judge(results)

    # Run LLM-as-judge
    try:
        scorecard = await run_trust_judge(transcript)
    except Exception as e:
        scorecard = TrustScorecard()
        scorecard.judge_commentary = f"Judge error: {e}"

    # Populate mechanical assertions from DOM signals
    # Use the first successful result that has DOM signals
    for result in results:
        if result.dom_signals.decision_summary_appeared or result.stop_reason != "error":
            populate_scorecard_from_result(scorecard, result)
            break

    scorecard.calculate_totals()
    scorecard.evaluate_gate()

    return results, scorecard


@app.command()
def trust(
    url: Annotated[str, typer.Argument(help="Target URL to test")],
    suite: Annotated[
        str,
        typer.Option("--suite", "-s", help="Trust test suite to run"),
    ] = "expertCouncil_adult_trust_v1",
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output directory for reports"),
    ] = None,
    personas: Annotated[
        str | None,
        typer.Option(
            "--personas",
            "-p",
            help="Comma-separated list of personas (default: all suite personas)",
        ),
    ] = None,
    headless: Annotated[
        bool,
        typer.Option("--headless/--no-headless", help="Run browser in headless mode"),
    ] = True,
    token: Annotated[
        str | None,
        typer.Option("--token", "-t", help="JWT session token for authentication"),
    ] = None,
) -> None:
    """Run a trust test suite against a target URL.

    This runs deterministic persona scripts to test whether the target
    application earns adult trust through authority, boundary enforcement,
    compression, professional tone, and clean exits.

    Example:
        ai-beta-test trust https://thinking-partner.test --suite expertCouncil_adult_trust_v1
    """
    from ai_beta_tester.suites.expertCouncil_adult_trust_v1.personas import list_trust_personas
    from ai_beta_tester.suites.expertCouncil_adult_trust_v1.runner import TrustRunResult

    # Load suite configuration
    try:
        suite_cls = get_suite(suite)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        available = list_suites()
        if available:
            console.print(f"Available suites: {', '.join(available)}")
        raise typer.Exit(1)

    suite_config = suite_cls.get_config()

    # Determine which personas to run
    if personas:
        persona_list = [p.strip() for p in personas.split(",")]
    else:
        persona_list = suite_config.personas

    # Validate personas exist in trust persona registry (not general personalities)
    available_trust_personas = list_trust_personas()
    for p in persona_list:
        if p not in available_trust_personas:
            console.print(f"[red]Unknown trust persona '{p}'[/red]")
            console.print(f"Available trust personas: {', '.join(available_trust_personas)}")
            raise typer.Exit(1)

    # Show session info
    console.print(
        Panel(
            f"[bold]Target:[/bold] {url}\n"
            f"[bold]Suite:[/bold] {suite} (v{suite_cls.version})\n"
            f"[bold]Personas:[/bold] {', '.join(persona_list)}\n"
            f"[bold]Max Duration:[/bold] {suite_config.max_duration_seconds}s\n"
            f"[bold]Mode:[/bold] Deterministic (scripted turns)",
            title="[bold blue]Trust Test Suite[/bold blue]",
        )
    )

    # Progress tracking
    progress_status = {"description": "Initializing..."}

    def update_progress(desc: str) -> None:
        progress_status["description"] = desc

    # Run the trust suite
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Running trust test suite...", total=None)

        def progress_callback(desc: str) -> None:
            progress.update(task, description=desc)

        try:
            results, scorecard = asyncio.run(
                _run_trust_suite(
                    url=url,
                    suite_cls=suite_cls,
                    persona_names=persona_list,
                    progress_callback=progress_callback,
                    headless=headless,
                    auth_token=token,
                )
            )
        except KeyboardInterrupt:
            console.print("\n[yellow]Trust test interrupted. Cleaning up...[/yellow]")
            _cleanup_playwright_browsers()
            raise typer.Exit(130)
        except Exception as e:
            console.print(f"[red]Trust test failed: {e}[/red]")
            _cleanup_playwright_browsers()
            raise typer.Exit(1)

        progress.update(task, description="Generating report...")

    # Generate report
    from ai_beta_tester.suites.expertCouncil_adult_trust_v1.runner import (
        format_transcript_for_judge,
        combine_results_for_judge,
    )

    output_dir = output or Path("./reports/trust")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate markdown report
    report_lines = _generate_trust_report(results, scorecard, suite_cls, url)

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"trust_report_{timestamp}.md"
    report_path.write_text("\n".join(report_lines))

    # Show results summary
    console.print()

    # Trust scorecard table
    scorecard_table = Table(title="Trust Scorecard")
    scorecard_table.add_column("Dimension", style="cyan")
    scorecard_table.add_column("Score", justify="center")
    scorecard_table.add_column("Max", justify="center", style="dim")

    dimensions = [
        ("Authority", scorecard.authority),
        ("Boundary Enforcement", scorecard.boundary_enforcement),
        ("Compression", scorecard.compression),
        ("Tone Maturity", scorecard.tone_maturity),
        ("Clean Exit", scorecard.clean_exit),
    ]

    for name, score in dimensions:
        style = "green" if score == 2 else "yellow" if score == 1 else "red"
        scorecard_table.add_row(name, f"[{style}]{score}[/{style}]", "2")

    console.print(scorecard_table)

    # Overall result
    total_style = "green" if scorecard.total_score >= 8 else "yellow" if scorecard.total_score >= 5 else "red"
    console.print(f"\n[bold]Total Score:[/bold] [{total_style}]{scorecard.total_score}/10[/{total_style}]")
    console.print(f"[bold]Trust Score (1-5):[/bold] {scorecard.trust_score_1to5}")

    gate_style = "green" if scorecard.pass_fail == "PASS" else "red"
    console.print(f"\n[bold]Gate:[/bold] [{gate_style}]{scorecard.pass_fail}[/{gate_style}]")

    if scorecard.failure_reasons:
        console.print("\n[red]Failure Reasons:[/red]")
        for reason in scorecard.failure_reasons:
            console.print(f"  - {reason}")

    # Persona results table
    console.print()
    table = Table(title="Persona Results")
    table.add_column("Persona", style="cyan")
    table.add_column("Status")
    table.add_column("Turns", justify="right")
    table.add_column("Duration", justify="right")
    table.add_column("Stop Reason")

    for result in results:
        status = "OK" if result.error is None else "ERROR"
        status_style = "green" if result.error is None else "red"
        turns = len([t for t in result.turns if t.role.value == "user"])
        duration = f"{result.duration_seconds:.1f}s"

        table.add_row(
            result.persona_name.replace("_", " ").title(),
            f"[{status_style}]{status}[/{status_style}]",
            str(turns),
            duration,
            result.stop_reason,
        )

    console.print(table)

    # DOM signals summary
    if results:
        first_result = results[0]
        signals = first_result.dom_signals
        console.print()
        console.print("[bold]DOM Signals:[/bold]")
        console.print(f"  Decision Summary: {'Yes' if signals.decision_summary_appeared else 'No'}")
        console.print(f"  End State: {signals.decision_end_state or 'Not detected'}")
        if signals.paywall_appeared:
            console.print(f"  Paywall: Appeared (outcome: {signals.payment_outcome or 'unknown'})")

    console.print(f"\n[dim]Report saved to: {report_path}[/dim]")


def _generate_trust_report(
    results: list,
    scorecard,
    suite_cls: type,
    target_url: str,
) -> list[str]:
    """Generate markdown report from trust test results."""
    from datetime import datetime
    from ai_beta_tester.suites.expertCouncil_adult_trust_v1.runner import TurnRole
    from ai_beta_tester.suites.expertCouncil_adult_trust_v1.scoring import EndState

    lines = []

    # Header
    lines.append("# Trust Test Report")
    lines.append("")
    lines.append(f"**Suite:** {suite_cls.name} (v{suite_cls.version})")
    lines.append(f"**Target:** {target_url}")
    lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # Verdict Banner
    lines.append("---")
    lines.append("")
    lines.append(f"## Verdict: {scorecard.pass_fail}")
    lines.append("")
    lines.append(f"**Trust Score:** {scorecard.total_score}/10")
    lines.append(f"**Trust Score (1-5):** {scorecard.trust_score_1to5}")
    lines.append(f"**End State:** {scorecard.end_state.value}")
    if scorecard.time_to_closure_seconds:
        lines.append(f"**Time to Closure:** {scorecard.time_to_closure_seconds:.0f}s")
    lines.append("")

    if scorecard.failure_reasons:
        lines.append("### Failure Reasons")
        for reason in scorecard.failure_reasons:
            lines.append(f"- {reason}")
        lines.append("")

    # Scorecard Table
    lines.append("## Trust Scorecard")
    lines.append("")
    lines.append("| Dimension | Score | Description |")
    lines.append("|-----------|-------|-------------|")

    dimension_descriptions = {
        "Authority": "Maintained calm, firm authority without defensiveness",
        "Boundary Enforcement": "Redirected loops, avoidance, and manipulation",
        "Compression": "Narrowed decision space toward actionable options",
        "Tone Maturity": "Professional tone, avoided therapy-speak",
        "Clean Exit": "Session ended in clear state (decision/defer/adjourn)",
    }

    dimensions = [
        ("Authority", scorecard.authority),
        ("Boundary Enforcement", scorecard.boundary_enforcement),
        ("Compression", scorecard.compression),
        ("Tone Maturity", scorecard.tone_maturity),
        ("Clean Exit", scorecard.clean_exit),
    ]

    for name, score in dimensions:
        score_display = f"{score}/2"
        if score == 0:
            score_display = f"**{score}/2** (FAIL)"
        lines.append(f"| {name} | {score_display} | {dimension_descriptions.get(name, '')} |")

    lines.append("")

    # DOM Signals
    lines.append("## Outcome Assertions (Mechanical)")
    lines.append("")
    lines.append("| Assertion | Result |")
    lines.append("|-----------|--------|")
    lines.append(f"| decision-summary appeared | {'Yes' if scorecard.decision_summary_appeared else 'No'} |")
    lines.append(f"| End state detected | {scorecard.end_state.value} |")

    if scorecard.end_state == EndState.DECISION:
        lines.append(f"| action-path present | {'Yes' if scorecard.action_path_present else 'No'} |")
    elif scorecard.end_state == EndState.DEFER:
        lines.append(f"| deferral-until present | {'Yes' if scorecard.deferral_until_present else 'No'} |")
    elif scorecard.end_state == EndState.ADJOURN:
        lines.append(f"| adjourn-reason present | {'Yes' if scorecard.adjourn_reason_present else 'No'} |")

    lines.append(f"| paywall-modal appeared | {'Yes' if scorecard.paywall_appeared else 'No'} |")
    if scorecard.payment_outcome:
        lines.append(f"| Payment outcome | {scorecard.payment_outcome} |")

    lines.append("")

    # Key Excerpts from Judge
    if scorecard.key_excerpts:
        lines.append("## Key Transcript Excerpts")
        lines.append("")
        lines.append("Evidence supporting the trust score:")
        lines.append("")
        for i, excerpt in enumerate(scorecard.key_excerpts, 1):
            lines.append(f"> {i}. \"{excerpt}\"")
            lines.append("")

    # Judge Commentary
    if scorecard.judge_commentary:
        lines.append("## Judge Commentary")
        lines.append("")
        lines.append(f"> {scorecard.judge_commentary}")
        lines.append("")

    # Per-Persona Details
    lines.append("## Persona Results")
    lines.append("")

    for result in results:
        lines.append(f"### {result.persona_name.replace('_', ' ').title()}")
        lines.append("")
        lines.append(f"**Decision Topic:** {result.decision_topic}")
        lines.append(f"**Duration:** {result.duration_seconds:.1f}s")
        lines.append(f"**Stop Reason:** {result.stop_reason}")

        if result.error:
            lines.append(f"**Error:** {result.error}")

        lines.append("")

        # Transcript
        if result.turns:
            lines.append("**Transcript:**")
            lines.append("")
            for turn in result.turns:
                role_prefix = "**User:**" if turn.role == TurnRole.USER else "**System:**"
                # Truncate long messages for readability
                content = turn.content
                if len(content) > 500:
                    content = content[:500] + "..."
                lines.append(f"{role_prefix} {content}")
                lines.append("")

        lines.append("---")
        lines.append("")

    return lines


@app.command()
def suites() -> None:
    """List available test suites."""
    available = list_suites()

    if not available:
        console.print("[yellow]No test suites available.[/yellow]")
        return

    table = Table(title="Available Test Suites")
    table.add_column("Name", style="cyan")
    table.add_column("Version")
    table.add_column("Description")

    for name in available:
        suite_cls = get_suite(name)
        table.add_row(name, suite_cls.version, suite_cls.description)

    console.print(table)


@app.command()
def ui(
    port: Annotated[
        int, typer.Option("--port", "-p", help="API server port")
    ] = 8765,
    no_browser: Annotated[
        bool, typer.Option("--no-browser", help="Don't open browser")
    ] = False,
) -> None:
    """Launch the web UI dashboard.

    Starts the FastAPI backend server. The Next.js frontend should be started
    separately with 'npm run dev' in the ui/ directory, or use the combined
    dev script.
    """
    import uvicorn
    import webbrowser

    console.print(
        Panel(
            f"[bold]API Server:[/bold] http://localhost:{port}\n"
            f"[bold]Dashboard:[/bold] http://ai-beta-tester.test/\n"
            f"\n[dim]Press Ctrl+C to stop[/dim]",
            title="[bold blue]AI Beta Tester UI[/bold blue]",
        )
    )

    if not no_browser:
        webbrowser.open("http://ai-beta-tester.test/")

    uvicorn.run(
        "ai_beta_tester.api.main:app",
        host="127.0.0.1",
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    app()
