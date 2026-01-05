"""Trust test report generator with scorecard and transcript excerpts."""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from ai_beta_tester.models import AgentRunStatus, Session
from ai_beta_tester.suites.expertCouncil_adult_trust_v1.scoring import TrustScorecard, EndState

if TYPE_CHECKING:
    from ai_beta_tester.suites.base import Suite


class TrustReporter:
    """Generates markdown reports for trust test sessions."""

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or Path("./reports/trust")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, session: Session, suite_cls: type["Suite"]) -> str:
        """Generate a markdown report for a trust test session."""
        lines: list[str] = []

        # Get scorecard from session (attached by CLI)
        scorecard: TrustScorecard = getattr(session, "trust_scorecard", TrustScorecard())

        # Header
        lines.append("# Trust Test Report")
        lines.append("")
        lines.append(f"**Suite:** {suite_cls.name} (v{suite_cls.version})")
        lines.append(f"**Target:** {session.target_url}")
        lines.append(f"**Date:** {session.started_at.strftime('%Y-%m-%d %H:%M') if session.started_at else 'N/A'}")
        if session.duration_seconds:
            lines.append(f"**Duration:** {self._format_duration(session.duration_seconds)}")
        lines.append("")

        # Trust Verdict Banner
        lines.append("---")
        lines.append("")
        gate_emoji = "PASS" if scorecard.pass_fail == "PASS" else "FAIL"
        lines.append(f"## Verdict: {gate_emoji}")
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

        # Trust Scorecard Table
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

        # Outcome Assertions (Mechanical)
        lines.append("## Outcome Assertions")
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

        # Key Excerpts
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

        # Persona Results
        lines.append("## Persona Results")
        lines.append("")
        lines.append("| Persona | Status | Actions | Findings | Dimension Tested |")
        lines.append("|---------|--------|---------|----------|------------------|")

        for run in session.agent_runs:
            status = run.status.value.title()
            # Get dimension from personality if available
            from ai_beta_tester.personalities import get_personality
            try:
                persona_cls = get_personality(run.personality)
                dimension = getattr(persona_cls, "tests_dimension", "general")
            except ValueError:
                dimension = "general"

            lines.append(
                f"| {run.personality.replace('_', ' ').title()} | {status} | "
                f"{run.action_count} | {run.finding_count} | {dimension} |"
            )

        lines.append("")

        # Per-Persona Details
        for run in session.agent_runs:
            lines.append(f"### {run.personality.replace('_', ' ').title()}")
            lines.append("")

            if run.verdict:
                v = run.verdict
                lines.append("**Verdict:**")
                lines.append(f"- Trust Score: {v.trust_level}/5")
                lines.append(f"- Would use again: {'Yes' if v.would_use_again else 'No' if v.would_use_again is False else 'Unknown'}")
                lines.append("")
                if v.commentary:
                    lines.append("**Commentary:**")
                    lines.append(f"> {v.commentary}")
                    lines.append("")

            # Action log for this persona
            if run.actions:
                lines.append("**Actions:**")
                for action in run.actions[:10]:  # Limit to first 10
                    step = action.to_reproduction_step()
                    lines.append(f"{action.sequence + 1}. {step}")
                if len(run.actions) > 10:
                    lines.append(f"... and {len(run.actions) - 10} more actions")
                lines.append("")

            # Findings
            if run.findings:
                lines.append("**Findings:**")
                for finding in run.findings:
                    lines.append(f"- [{finding.severity.value.upper()}] {finding.title}")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Full Action Log
        lines.append("## Full Action Log")
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

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable form."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        minutes = seconds / 60
        if minutes < 60:
            return f"{minutes:.0f}m {seconds % 60:.0f}s"
        hours = minutes / 60
        return f"{hours:.0f}h {minutes % 60:.0f}m"

    def save(self, session: Session, suite_cls: type["Suite"], filename: str | None = None) -> Path:
        """Generate and save a trust report to a file."""
        report = self.generate(session, suite_cls)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trust_report_{timestamp}.md"

        filepath = self.output_dir / filename
        filepath.write_text(report)
        return filepath
