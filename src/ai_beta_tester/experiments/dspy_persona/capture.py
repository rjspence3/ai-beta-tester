"""Transcript capture during test sessions.

Provides utilities for capturing full conversation transcripts
during orchestrator runs via event callbacks.
"""

from ai_beta_tester.orchestrator import Orchestrator, OrchestratorConfig
from ai_beta_tester.models import Session

from .transcript import ConversationTranscript
from .dynamic_personality import PersonalityContextManager


async def run_with_transcript_capture(
    orchestrator: Orchestrator,
    target_url: str,
    goal: str,
    personality: str,
    session_config=None,
) -> tuple[Session, ConversationTranscript]:
    """Run a session and capture transcript via event callback.

    Args:
        orchestrator: The Orchestrator instance
        target_url: URL to test
        goal: Testing goal
        personality: Personality name to use
        session_config: Optional session configuration

    Returns:
        Tuple of (session, transcript)
    """
    transcript = ConversationTranscript(
        persona_name=personality,
        target_url=target_url,
    )

    async def capture_events(event_type: str, data: dict):
        """Event callback to capture messages."""

        if event_type == "action_taken":
            action_type = data.get("action_type")
            params = data.get("parameters", {})

            # Capture typed messages (agent's chat messages)
            if action_type == "type":
                # Handle both naming conventions:
                # - Original: element, ref, text
                # - Playwright MCP: selector, value
                element = params.get("element", "") or params.get("selector", "") or ""
                ref = params.get("ref", "") or ""
                text = params.get("text", "") or params.get("value", "") or ""

                element = element.lower()
                ref = ref.lower()

                # Check if this looks like a chat input
                chat_indicators = ["chat", "message", "input", "compose", "send", "textarea", "contenteditable"]
                is_chat = any(ind in element or ind in ref for ind in chat_indicators)

                # If we have text and it looks like chat OR we have no element info (permissive capture)
                if text and (is_chat or not element):
                    transcript.add_agent_message(text)

    session = await orchestrator.run_session(
        target_url=target_url,
        goal=goal,
        personalities=[personality],
        session_config=session_config,
        event_callback=capture_events,
    )

    transcript.session_id = str(session.id)

    return session, transcript


async def run_with_custom_prompt_and_capture(
    orchestrator: Orchestrator,
    target_url: str,
    goal: str,
    base_personality: str,
    custom_prompt: str,
    session_config=None,
) -> tuple[Session, ConversationTranscript]:
    """Run a session with a custom prompt and capture transcript.

    This combines dynamic personality creation with transcript capture.

    Args:
        orchestrator: The Orchestrator instance
        target_url: URL to test
        goal: Testing goal
        base_personality: Base personality name
        custom_prompt: Custom system prompt to use
        session_config: Optional session configuration

    Returns:
        Tuple of (session, transcript)
    """
    temp_name = f"{base_personality}_experiment_{id(custom_prompt) % 10000}"

    transcript = ConversationTranscript(
        persona_name=f"{base_personality} (optimized)",
        target_url=target_url,
    )

    async def capture_events(event_type: str, data: dict):
        """Event callback to capture messages."""

        if event_type == "action_taken":
            action_type = data.get("action_type")
            params = data.get("parameters", {})

            if action_type == "type":
                # Handle both naming conventions:
                # - Original: element, ref, text
                # - Playwright MCP: selector, value
                element = params.get("element", "") or params.get("selector", "") or ""
                ref = params.get("ref", "") or ""
                text = params.get("text", "") or params.get("value", "") or ""

                element = element.lower()
                ref = ref.lower()

                # Check if this looks like a chat input
                chat_indicators = ["chat", "message", "input", "compose", "send", "textarea", "contenteditable"]
                is_chat = any(ind in element or ind in ref for ind in chat_indicators)

                # If we have text and it looks like chat OR we have no element info (permissive capture)
                if text and (is_chat or not element):
                    transcript.add_agent_message(text)

    with PersonalityContextManager(base_personality, custom_prompt, temp_name):
        session = await orchestrator.run_session(
            target_url=target_url,
            goal=goal,
            personalities=[temp_name],
            session_config=session_config,
            event_callback=capture_events,
        )

    transcript.session_id = str(session.id)

    return session, transcript


def extract_transcript_from_session(session: Session, persona_name: str = "") -> ConversationTranscript:
    """Extract transcript from a completed session.

    This is a fallback for when event capture wasn't used.
    Only captures agent messages from actions, not system responses.

    Args:
        session: Completed session
        persona_name: Name of the persona used

    Returns:
        ConversationTranscript (partial - agent messages only)
    """
    transcript = ConversationTranscript(
        persona_name=persona_name or "unknown",
        target_url=session.target_url,
        session_id=str(session.id),
    )

    for run in session.agent_runs:
        for action in run.actions:
            if action.action_type.value == "type":
                element = action.parameters.get("element", "").lower()
                text = action.parameters.get("text", "")

                chat_indicators = ["chat", "message", "input"]
                is_chat = any(ind in element for ind in chat_indicators)

                if is_chat and text:
                    transcript.add_agent_message(text)

    return transcript
