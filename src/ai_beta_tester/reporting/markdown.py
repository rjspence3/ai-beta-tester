"""Markdown report generator."""

from datetime import datetime
from pathlib import Path

from ai_beta_tester.models import (
    AgentRunStatus,
    Finding,
    FindingSeverity,
    Session,
)


class MarkdownReporter:
    """Generates markdown reports from test sessions."""

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or Path("./reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, session: Session) -> str:
        """Generate a markdown report for a session."""
        lines: list[str] = []

        # Header
        lines.append(f"# Beta Test Report: {session.goal}")
        lines.append("")
        lines.append(f"**Target:** {session.target_url}")
        lines.append(f"**Goal:** {session.goal}")
        lines.append(f"**Date:** {session.started_at.strftime('%Y-%m-%d %H:%M') if session.started_at else 'N/A'}")
        if session.duration_seconds:
            duration = self._format_duration(session.duration_seconds)
            lines.append(f"**Duration:** {duration}")
        lines.append("")

        # Agent summary table
        lines.append("## Agents")
        lines.append("")
        lines.append("| Personality | Status | Actions | Findings |")
        lines.append("|-------------|--------|---------|----------|")
        for run in session.agent_runs:
            status = run.status.value.title()
            lines.append(
                f"| {run.personality.replace('_', ' ').title()} | {status} | {run.action_count} | {run.finding_count} |"
            )
        lines.append("")

        # Session summary
        lines.append("## Summary")
        lines.append("")
        total_findings = sum(run.finding_count for run in session.agent_runs)
        total_agents = len(session.agent_runs)
        stuck = sum(1 for run in session.agent_runs if run.status == AgentRunStatus.STUCK)

        summary_parts = [f"{total_agents} agent(s) tested the application."]
        if stuck > 0:
            summary_parts.append(f"{stuck} got stuck.")
        if total_findings > 0:
            summary_parts.append(f"Found {total_findings} issue(s).")
        else:
            summary_parts.append("No issues found.")

        lines.append(" ".join(summary_parts))
        lines.append("")

        # Findings by severity
        all_findings = [f for run in session.agent_runs for f in run.findings]
        if all_findings:
            lines.append("## Findings")
            lines.append("")

            for severity in FindingSeverity:
                severity_findings = [f for f in all_findings if f.severity == severity]
                if severity_findings:
                    lines.append(f"### {severity.value.title()} ({len(severity_findings)})")
                    lines.append("")
                    for finding in severity_findings:
                        lines.extend(self._format_finding(finding, session))
                        lines.append("")

        # Action log per agent
        lines.append("## Action Log")
        lines.append("")
        for run in session.agent_runs:
            lines.append(f"### {run.personality.replace('_', ' ').title()}")
            lines.append("")
            if run.actions:
                for action in run.actions:
                    step = action.to_reproduction_step()
                    lines.append(f"{action.sequence + 1}. {step}")
            else:
                lines.append("No actions recorded.")
            lines.append("")

        return "\n".join(lines)

    def _format_finding(self, finding: Finding, session: Session) -> list[str]:
        """Format a single finding."""
        lines: list[str] = []

        # Find which agent found this
        agent_name = "Unknown"
        for run in session.agent_runs:
            if any(f.id == finding.id for f in run.findings):
                agent_name = run.personality.replace("_", " ").title()
                break

        category_label = finding.category.value.upper().replace("_", " ")
        lines.append(f"#### [{category_label}] {finding.title}")
        lines.append(f"**Found by:** {agent_name}")
        lines.append(f"**Severity:** {finding.severity.value.title()}")
        lines.append("")
        lines.append(finding.description)

        if finding.reproduction_steps:
            lines.append("")
            lines.append("**Reproduction Steps:**")
            for i, step in enumerate(finding.reproduction_steps, 1):
                lines.append(f"{i}. {step}")

        if finding.screenshot_path:
            lines.append("")
            lines.append(f"**Screenshot:** ![Finding]({finding.screenshot_path})")

        lines.append("")
        lines.append("---")

        return lines

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable form."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        minutes = seconds / 60
        if minutes < 60:
            return f"{minutes:.0f}m {seconds % 60:.0f}s"
        hours = minutes / 60
        return f"{hours:.0f}h {minutes % 60:.0f}m"

    def save(self, session: Session, filename: str | None = None) -> Path:
        """Generate and save a report to a file."""
        report = self.generate(session)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.md"

        filepath = self.output_dir / filename
        filepath.write_text(report)
        return filepath
