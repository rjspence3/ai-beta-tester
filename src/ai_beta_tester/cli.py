"""Command-line interface for AI Beta Tester."""

import asyncio
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

app = typer.Typer(
    name="ai-beta-test",
    help="AI-powered exploratory testing with distinct agent personalities",
    no_args_is_help=True,
)
console = Console()


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
        except Exception as e:
            console.print(f"[red]Session failed: {e}[/red]")
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


if __name__ == "__main__":
    app()
