"""Deterministic runner for trust test personas.

Unlike the Orchestrator (LLM-driven exploration), TrustRunner:
- Executes exact turn scripts from TrustPersona
- Captures actual conversation content
- Inspects DOM for mechanical assertions
- Does not improvise or make decisions
"""

from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

from ai_beta_tester.suites.expertCouncil_adult_trust_v1.personas import (
    TrustPersona,
    TurnScript,
)
from ai_beta_tester.suites.expertCouncil_adult_trust_v1.scoring import (
    TrustScorecard,
    EndState,
)


class TurnRole(Enum):
    """Role in conversation turn."""
    USER = "user"
    SYSTEM = "system"


@dataclass
class ChatTurn:
    """A single turn in the conversation."""
    role: TurnRole
    content: str
    turn_number: int
    timestamp: float  # seconds since session start
    intent: str = ""  # from TurnScript, for debugging


@dataclass
class DOMSignals:
    """Mechanical assertions from DOM inspection."""
    decision_summary_appeared: bool = False
    decision_end_state: str | None = None
    action_path_present: bool = False
    action_path_text: str | None = None
    deferral_until_present: bool = False
    deferral_until_text: str | None = None
    adjourn_reason_present: bool = False
    adjourn_reason_text: str | None = None
    paywall_appeared: bool = False
    payment_outcome: str | None = None  # "success" | "failure" | None
    session_credits_remaining: int | None = None


@dataclass
class TrustRunResult:
    """Result of a single persona's trust test run."""
    persona_name: str
    decision_topic: str
    turns: list[ChatTurn] = field(default_factory=list)
    dom_signals: DOMSignals = field(default_factory=DOMSignals)
    duration_seconds: float = 0.0
    completed_all_turns: bool = False
    stop_reason: str = ""  # "decision_summary" | "max_turns" | "timeout" | "error"
    error: str | None = None


class TrustRunner:
    """Deterministic runner for trust test personas.

    Executes scripted turn sequences against a target application,
    capturing conversation content and DOM state for evaluation.
    """

    def __init__(
        self,
        selectors: dict[str, str],
        timeout_seconds: int = 360,
        turn_timeout_ms: int = 90000,
        stability_checks: int = 3,
        stability_interval_ms: int = 1000,
        debug: bool = False,
    ) -> None:
        """Initialize the runner.

        Args:
            selectors: Dict of selector names to CSS selectors
            timeout_seconds: Max total time for persona run
            turn_timeout_ms: Max time to wait for system response per turn (90s for real API)
            stability_checks: Number of stable checks before considering response complete
            stability_interval_ms: Interval between stability checks
            debug: If True, capture screenshots and DOM dumps on errors
        """
        self.selectors = selectors
        self.timeout_seconds = timeout_seconds
        self.turn_timeout_ms = turn_timeout_ms
        self.stability_checks = stability_checks
        self.stability_interval_ms = stability_interval_ms
        self.debug = debug

    async def run_persona(
        self,
        page: "Page",
        persona: type[TrustPersona],
    ) -> TrustRunResult:
        """Execute a trust persona's deterministic script.

        Args:
            page: Playwright page, already navigated to target URL
            persona: TrustPersona class (not instance) to execute

        Returns:
            TrustRunResult with captured transcript and DOM signals
        """
        start_time = time()
        result = TrustRunResult(
            persona_name=persona.name,
            decision_topic=persona.decision_topic,
        )

        try:
            # Step 1: Get baseline content before starting
            baseline_content = await self._get_chat_content_hash(page)

            # Step 2: Enter decision topic and start session
            await self._enter_decision_topic(page, persona.decision_topic)

            # Step 3: Wait for and capture initial system message
            initial_response = await self._wait_for_system_response(page, baseline_content)
            result.turns.append(ChatTurn(
                role=TurnRole.SYSTEM,
                content=initial_response,
                turn_number=0,
                timestamp=time() - start_time,
            ))

            # Step 3: Execute each turn in the script
            for turn in persona.turns:
                # Check timeout
                elapsed = time() - start_time
                if elapsed > self.timeout_seconds:
                    result.stop_reason = "timeout"
                    break

                # Check stop condition before sending
                should_stop, reason = await self._check_stop_condition(
                    page, persona, turn.turn_number - 1
                )
                if should_stop:
                    result.stop_reason = reason
                    break

                # Execute the turn
                system_response = await self._execute_turn(page, turn, start_time, result)

                if system_response is None:
                    # Turn execution failed
                    break

            else:
                # All turns completed without breaking
                result.completed_all_turns = True
                result.stop_reason = "max_turns"

            # Step 4: Final stop condition check
            if not result.stop_reason:
                _, reason = await self._check_stop_condition(
                    page, persona, len(persona.turns)
                )
                result.stop_reason = reason or "completed"

            # Step 5: Inspect DOM for mechanical assertions
            result.dom_signals = await self._inspect_dom_signals(page)

        except Exception as e:
            result.error = str(e)
            result.stop_reason = "error"
            # Still try to capture DOM signals on error
            try:
                result.dom_signals = await self._inspect_dom_signals(page)
            except Exception:
                pass

        result.duration_seconds = time() - start_time
        return result

    async def _enter_decision_topic(
        self,
        page: "Page",
        topic: str,
    ) -> None:
        """Type topic and start the council session.

        Expert Council has two modes:
        1. Fresh session: Uses topic_input + start_council_button
        2. Existing session: Uses chat_input + send_button

        We check which mode we're in and use the appropriate selectors.
        After starting, waits for the council to begin responding.
        """
        # Check if we're in fresh session mode (topic_input visible)
        if "topic_input" in self.selectors:
            topic_input = page.locator(self.selectors["topic_input"])
            if await topic_input.count() > 0 and await topic_input.is_visible():
                # Fresh session mode - use topic_input and start_council_button
                await topic_input.fill(topic)

                start_button = page.locator(self.selectors["start_council_button"])
                await start_button.click()

                # Wait for chat container to appear
                chat_container = page.locator(self.selectors["chat_container"])
                await chat_container.wait_for(state="visible", timeout=self.turn_timeout_ms)

                # Wait briefly for council to start (streaming indicator or first content)
                await self._wait_for_council_start(page)
                return

        # Existing session mode - use chat_input and send_button
        chat_input = page.locator(self.selectors["chat_input"])
        send_button = page.locator(self.selectors["send_button"])

        await chat_input.wait_for(state="visible", timeout=self.turn_timeout_ms)
        await chat_input.fill(topic)
        await send_button.click()

        chat_container = page.locator(self.selectors["chat_container"])
        await chat_container.wait_for(state="visible", timeout=self.turn_timeout_ms)

        # Wait briefly for council to start
        await self._wait_for_council_start(page)

    async def _wait_for_council_start(self, page: "Page") -> None:
        """Wait for the council to start responding after topic entry.

        Detects either:
        - Streaming/thinking indicator appears
        - First system message appears
        - Decision summary appears (mock mode)

        Times out silently after 10 seconds - the main response wait will handle it.
        """
        deadline = time() + 10  # 10 second timeout for startup

        while time() < deadline:
            # Check if streaming started
            if await self._is_streaming(page):
                return

            # Check if decision_summary appeared (mock mode)
            if "decision_summary" in self.selectors:
                decision_summary = page.locator(self.selectors["decision_summary"])
                if await decision_summary.count() > 0:
                    return

            # Check if any system message appeared
            if "system_message" in self.selectors:
                system_messages = page.locator(self.selectors["system_message"])
                if await system_messages.count() > 0:
                    return

            await page.wait_for_timeout(500)

    async def _execute_turn(
        self,
        page: "Page",
        turn: TurnScript,
        start_time: float,
        result: TrustRunResult,
    ) -> str | None:
        """Execute one user turn and capture system response.

        Args:
            page: Playwright page
            turn: The turn script to execute
            start_time: Session start time for timestamp calculation
            result: TrustRunResult to append turns to

        Returns:
            System response content, or None if failed
        """
        try:
            # Get baseline content before sending (for change detection)
            baseline_content = await self._get_chat_content_hash(page)

            # Record user turn
            result.turns.append(ChatTurn(
                role=TurnRole.USER,
                content=turn.message,
                turn_number=turn.turn_number,
                timestamp=time() - start_time,
                intent=turn.intent,
            ))

            # Type and send message
            # Wait longer for chat input - it may be hidden during AI response
            chat_input = page.locator(self.selectors["chat_input"])
            send_button = page.locator(self.selectors["send_button"])

            # Wait for input with extended timeout (may be hidden during generation)
            try:
                await chat_input.wait_for(state="visible", timeout=self.turn_timeout_ms)
            except Exception:
                # Input not visible - check if we hit decision_summary (session ended)
                if "decision_summary" in self.selectors:
                    decision_summary = page.locator(self.selectors["decision_summary"])
                    if await decision_summary.count() > 0:
                        # Session ended with decision - record it and stop
                        content = (await decision_summary.inner_text()).strip()
                        result.turns.append(ChatTurn(
                            role=TurnRole.SYSTEM,
                            content=content,
                            turn_number=turn.turn_number,
                            timestamp=time() - start_time,
                        ))
                        return content
                raise

            await chat_input.fill(turn.message)
            await send_button.click()

            # Wait for and capture system response (using content change detection)
            system_response = await self._wait_for_system_response(page, baseline_content)

            result.turns.append(ChatTurn(
                role=TurnRole.SYSTEM,
                content=system_response,
                turn_number=turn.turn_number,
                timestamp=time() - start_time,
            ))

            return system_response

        except Exception as e:
            result.error = f"Turn {turn.turn_number} failed: {e}"
            result.stop_reason = "error"
            return None

    async def _count_system_messages(self, page: "Page") -> int:
        """Count current system messages in chat.

        Counts actual chat messages from the system/AI, not just decision_summary.
        Falls back to decision_summary count if no message selector available.
        """
        # Try system_message selector first (individual AI responses)
        if "system_message" in self.selectors:
            system_messages = page.locator(self.selectors["system_message"])
            count = await system_messages.count()
            if count > 0:
                return count

        # Try generic chat_message selector
        if "chat_message" in self.selectors:
            chat_messages = page.locator(self.selectors["chat_message"])
            return await chat_messages.count()

        # Fallback: count decision_summary
        if "decision_summary" in self.selectors:
            decision_summary = page.locator(self.selectors["decision_summary"])
            return await decision_summary.count()

        return 0

    async def _is_streaming(self, page: "Page") -> bool:
        """Check if the system is currently streaming a response."""
        for indicator in ["streaming_indicator", "thinking_indicator"]:
            if indicator in self.selectors:
                loc = page.locator(self.selectors[indicator])
                if await loc.count() > 0 and await loc.is_visible():
                    return True
        return False

    async def _get_latest_system_content(self, page: "Page") -> str:
        """Get the content of the latest system message."""
        # Try to get the last system message
        if "system_message" in self.selectors:
            system_messages = page.locator(self.selectors["system_message"])
            count = await system_messages.count()
            if count > 0:
                last_message = system_messages.nth(count - 1)
                return (await last_message.inner_text()).strip()

        # Try decision summary (might appear as the response)
        if "decision_summary" in self.selectors:
            decision_summary = page.locator(self.selectors["decision_summary"])
            if await decision_summary.count() > 0:
                return (await decision_summary.inner_text()).strip()

        # Try chat container as fallback
        if "chat_container" in self.selectors:
            chat_container = page.locator(self.selectors["chat_container"])
            if await chat_container.count() > 0:
                content = (await chat_container.inner_text()).strip()
                # Remove extra whitespace but keep the content
                content = " ".join(content.split())
                return content

        return ""

    async def _get_chat_content_hash(self, page: "Page") -> str:
        """Get a hash/fingerprint of the chat content for change detection."""
        if "chat_container" in self.selectors:
            chat_container = page.locator(self.selectors["chat_container"])
            if await chat_container.count() > 0:
                return (await chat_container.inner_text()).strip()
        return ""

    async def _wait_for_system_response(
        self,
        page: "Page",
        previous_content_or_count,
    ) -> str:
        """Wait for system response and return content.

        Handles both mock mode (instant decision_summary) and real API mode
        (streaming responses that take time). Uses multiple detection strategies:
        1. decision_summary appearance (mock mode shortcut)
        2. Content change detection (real API)
        3. Streaming indicator completion

        Args:
            page: Playwright page
            previous_content_or_count: Previous content hash or message count

        Returns:
            Text content of the response
        """
        deadline = time() + (self.turn_timeout_ms / 1000)

        # Get baseline content for change detection
        if isinstance(previous_content_or_count, str):
            baseline_content = previous_content_or_count
        else:
            baseline_content = await self._get_chat_content_hash(page)

        # Phase 1: Wait for new content to appear
        content_changed = False
        while time() < deadline:
            # Check decision_summary first (mock mode shortcut)
            if "decision_summary" in self.selectors:
                decision_summary = page.locator(self.selectors["decision_summary"])
                if await decision_summary.count() > 0:
                    # Decision summary appeared - wait for it to stabilize
                    return await self._wait_for_stable_content(
                        page, decision_summary, deadline
                    )

            # Check for content changes (real API response)
            current_content = await self._get_chat_content_hash(page)
            if current_content != baseline_content and len(current_content) > len(baseline_content):
                content_changed = True
                break

            # Check if streaming started (indicates response is coming)
            if await self._is_streaming(page):
                content_changed = True
                break

            await page.wait_for_timeout(500)

        if not content_changed and time() >= deadline:
            # Timeout - return whatever content we have
            content = await self._get_latest_system_content(page)
            if content:
                return content
            raise TimeoutError(
                f"No system response after {self.turn_timeout_ms}ms"
            )

        # Phase 2: Wait for streaming to complete
        while time() < deadline and await self._is_streaming(page):
            await page.wait_for_timeout(500)

        # Phase 3: Wait for content to stabilize
        last_content = ""
        stable_count = 0

        while stable_count < self.stability_checks and time() < deadline:
            await page.wait_for_timeout(self.stability_interval_ms)

            # Check if decision_summary appeared during stabilization
            if "decision_summary" in self.selectors:
                decision_summary = page.locator(self.selectors["decision_summary"])
                if await decision_summary.count() > 0:
                    return await self._wait_for_stable_content(
                        page, decision_summary, deadline
                    )

            current_content = await self._get_chat_content_hash(page)

            if current_content == last_content and current_content.strip():
                stable_count += 1
            else:
                last_content = current_content
                stable_count = 0

        # Return the filtered content (not the raw hash)
        return await self._get_latest_system_content(page)

    async def _wait_for_stable_content(
        self,
        page: "Page",
        locator,
        deadline: float,
    ) -> str:
        """Wait for a locator's content to stabilize."""
        last_content = ""
        stable_count = 0

        while stable_count < self.stability_checks and time() < deadline:
            await page.wait_for_timeout(self.stability_interval_ms)
            current_content = (await locator.inner_text()).strip()

            if current_content == last_content and current_content:
                stable_count += 1
            else:
                last_content = current_content
                stable_count = 0

        return last_content

    async def _check_stop_condition(
        self,
        page: "Page",
        persona: type[TrustPersona],
        turns_completed: int,
    ) -> tuple[bool, str]:
        """Check if we should stop execution.

        Args:
            page: Playwright page
            persona: TrustPersona being executed
            turns_completed: Number of turns already completed

        Returns:
            Tuple of (should_stop, reason)
        """
        # Check if decision-summary appeared
        decision_summary = page.locator(self.selectors["decision_summary"])
        if await decision_summary.count() > 0:
            return (True, "decision_summary")

        # Check max turns from persona script
        max_turns = len(persona.turns)
        if turns_completed >= max_turns:
            return (True, "max_turns")

        return (False, "")

    async def _inspect_dom_signals(self, page: "Page") -> DOMSignals:
        """Capture mechanical assertions from DOM state.

        Inspects the page for presence of key elements that indicate
        session outcome (decision reached, deferred, adjourned, etc.)
        """
        signals = DOMSignals()

        async def exists(selector_name: str) -> bool:
            """Check if element exists by selector name."""
            if selector_name not in self.selectors:
                return False
            return await page.locator(self.selectors[selector_name]).count() > 0

        async def get_text(selector_name: str) -> str | None:
            """Get text content of element if it exists."""
            if selector_name not in self.selectors:
                return None
            loc = page.locator(self.selectors[selector_name])
            if await loc.count() > 0:
                return (await loc.inner_text()).strip()
            return None

        # Decision summary
        signals.decision_summary_appeared = await exists("decision_summary")
        signals.decision_end_state = await get_text("decision_end_state")

        # Action path (for DECISION end state)
        signals.action_path_present = await exists("action_path")
        signals.action_path_text = await get_text("action_path")

        # Deferral (for DEFER end state)
        signals.deferral_until_present = await exists("deferral_until")
        signals.deferral_until_text = await get_text("deferral_until")

        # Adjournment (for ADJOURN end state)
        signals.adjourn_reason_present = await exists("adjourn_reason")
        signals.adjourn_reason_text = await get_text("adjourn_reason")

        # Paywall / payment
        signals.paywall_appeared = await exists("paywall_modal")

        if await exists("payment_success"):
            signals.payment_outcome = "success"
        elif await exists("payment_failure"):
            signals.payment_outcome = "failure"

        # Session credits
        credits_text = await get_text("session_credits_remaining")
        if credits_text:
            import re
            match = re.search(r"(\d+)", credits_text)
            if match:
                signals.session_credits_remaining = int(match.group(1))

        return signals


def format_transcript_for_judge(result: TrustRunResult) -> str:
    """Format captured turns into judge-readable transcript.

    Produces output matching the format expected by TRUST_JUDGE_PROMPT.
    """
    lines = [f"=== Persona: {result.persona_name} ==="]
    lines.append(f"Decision Topic: {result.decision_topic}")
    lines.append("")

    for turn in result.turns:
        if turn.role == TurnRole.USER:
            lines.append(f"User: {turn.content}")
        else:
            lines.append(f"System: {turn.content}")
        lines.append("")

    lines.append(f"[Session ended - {result.stop_reason}]")

    return "\n".join(lines)


def populate_scorecard_from_result(
    scorecard: TrustScorecard,
    result: TrustRunResult,
) -> None:
    """Copy mechanical assertions from DOM inspection into scorecard.

    Args:
        scorecard: TrustScorecard to populate
        result: TrustRunResult with DOM signals
    """
    signals = result.dom_signals

    scorecard.decision_summary_appeared = signals.decision_summary_appeared
    scorecard.action_path_present = signals.action_path_present
    scorecard.deferral_until_present = signals.deferral_until_present
    scorecard.adjourn_reason_present = signals.adjourn_reason_present
    scorecard.paywall_appeared = signals.paywall_appeared
    scorecard.payment_outcome = signals.payment_outcome
    scorecard.time_to_closure_seconds = result.duration_seconds

    # Infer end state from DOM signals if judge didn't set it
    if scorecard.end_state == EndState.NONE and signals.decision_end_state:
        state_str = signals.decision_end_state.upper()
        try:
            scorecard.end_state = EndState(state_str)
        except ValueError:
            pass


def combine_results_for_judge(results: list[TrustRunResult]) -> str:
    """Combine multiple persona results into single transcript for judge.

    Used when running all 5 personas and wanting a combined evaluation.
    """
    transcripts = [format_transcript_for_judge(r) for r in results]
    return "\n\n---\n\n".join(transcripts)
