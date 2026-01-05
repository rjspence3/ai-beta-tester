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

        # Scoring
        if session.aggregate_score:
            agg = session.aggregate_score
            lines.append("## Release Gate")
            lines.append("")
            
            gate_emoji = "✅" if agg.pass_fail == "PASS" else "❌"
            lines.append(f"**Overall Status:** {gate_emoji} {agg.pass_fail}")
            lines.append("")
            
            if agg.gating_failures:
                lines.append("**Gating Failures:**")
                for fail in agg.gating_failures:
                    lines.append(f"- {fail}")
                lines.append("")
                
            lines.append(f"**Overall Score:** {agg.overall_score}/100")
            lines.append("")
            
            # Per-Agent Score Table
            lines.append("### Per-Agent Scores")
            lines.append("")
            # Header
            header = "| Agent | Gate | Overall | Functional | UX | Legibility | Recovery | Perf | Trust |"
            lines.append(header)
            lines.append("|---|---|---|---|---|---|---|---|---|")
            
            for personality, score in agg.agent_scores.items():
                row = [
                    personality.replace("_", " ").title(),
                    score.pass_fail,
                    str(score.overall_score),
                    str(score.category_scores.get("Functional Reliability", 0)),
                    str(score.category_scores.get("UX Clarity & Friction", 0)),
                    str(score.category_scores.get("Feedback & State Legibility", 0)),
                    str(score.category_scores.get("Error Handling & Recovery", 0)),
                    str(score.category_scores.get("Performance Perception", 0)),
                    str(score.category_scores.get("Safety & Trust Signals", 0)),
                ]
                lines.append(f"| {' | '.join(row)} |")
            lines.append("")

        # Agent summary table
        lines.append("## Agents Summary")
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

        # Agent Verdicts
        for run in session.agent_runs:
            if run.verdict:
                v = run.verdict
                lines.append(f"## Agent Verdict ({run.personality.replace('_', ' ').title()})")
                lines.append("")
                lines.append("| Question | Answer |")
                lines.append("|---|---|")
                
                first_screen = "Yes" if v.first_screen_acceptable is True else "No" if v.first_screen_acceptable is False else "Unknown"
                lines.append(f"| First screen acceptable | {first_screen} |")
                
                overrides = str(v.override_count)
                if v.override_reasons:
                    overrides += f" ({'; '.join(v.override_reasons)})"
                lines.append(f"| Overrides | {overrides} |")
                
                lines.append(f"| Cognitive load | {v.cognitive_load.value.title()} |")
                lines.append(f"| Trust level | {v.trust_level} |")
                
                use_again = "Yes" if v.would_use_again is True else "No" if v.would_use_again is False else "Unknown"
                lines.append(f"| Would use again | {use_again} |")
                
                lines.append("")
                lines.append("**Commentary:**")
                lines.append(f"> \"{v.commentary or 'No commentary provided'}\"")
                lines.append("")
                lines.append("---")
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
        """Generate and save a report to a file.

        Reports are organized by target app:
            reports/<app-slug>/report_<agents>_<timestamp>.md

        Example:
            reports/expert-council/report_speedrunner_20251230_133329.md
            reports/expert-council/report_multi-agent-17_20251230_140000.md
        """
        report = self.generate(session)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Extract app slug from target URL
            app_slug = self._extract_app_slug(session.target_url)

            # Build agent descriptor
            agent_names = [run.personality for run in session.agent_runs]
            if len(agent_names) == 1:
                agent_desc = agent_names[0]
            elif len(agent_names) <= 3:
                agent_desc = "-".join(agent_names)
            else:
                agent_desc = f"multi-agent-{len(agent_names)}"

            filename = f"report_{agent_desc}_{timestamp}.md"

            # Create app-specific subdirectory
            app_dir = self.output_dir / app_slug
            app_dir.mkdir(parents=True, exist_ok=True)
            filepath = app_dir / filename
        else:
            filepath = self.output_dir / filename

        filepath.write_text(report)
        return filepath

    def _extract_app_slug(self, url: str) -> str:
        """Extract a clean app name from URL for directory naming."""
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or "unknown"

            # Remove common suffixes
            slug = hostname.replace(".test", "").replace(".local", "").replace(".localhost", "")
            slug = slug.replace("www.", "")

            # Handle localhost with port
            if slug in ("localhost", "127.0.0.1"):
                port = parsed.port
                slug = f"localhost-{port}" if port else "localhost"

            # Clean up for filesystem
            slug = slug.replace(".", "-").replace(":", "-")

            return slug or "unknown"
        except Exception:
            return "unknown"
