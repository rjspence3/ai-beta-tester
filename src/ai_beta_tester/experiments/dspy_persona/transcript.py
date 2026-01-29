"""Conversation transcript capture and storage."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Speaker(Enum):
    """Who sent the message."""
    AGENT = "agent"      # The AI tester persona
    SYSTEM = "system"    # The system being tested (e.g., Thinking Partner)


@dataclass
class TranscriptEntry:
    """A single message in the conversation."""
    speaker: Speaker
    message: str
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        label = self.speaker.value.upper()
        return f"[{label}]: {self.message}"


@dataclass
class ConversationTranscript:
    """Full conversation transcript between agent and system."""

    entries: list[TranscriptEntry] = field(default_factory=list)
    persona_name: str = ""
    target_url: str = ""
    session_id: str = ""
    started_at: datetime = field(default_factory=datetime.now)

    def add_agent_message(self, message: str) -> None:
        """Record a message sent by the agent."""
        self.entries.append(TranscriptEntry(Speaker.AGENT, message.strip()))

    def add_system_response(self, message: str) -> None:
        """Record a response from the system being tested."""
        self.entries.append(TranscriptEntry(Speaker.SYSTEM, message.strip()))

    @property
    def agent_messages(self) -> list[str]:
        """Get all agent messages."""
        return [e.message for e in self.entries if e.speaker == Speaker.AGENT]

    @property
    def system_messages(self) -> list[str]:
        """Get all system responses."""
        return [e.message for e in self.entries if e.speaker == Speaker.SYSTEM]

    @property
    def turn_count(self) -> int:
        """Number of agent turns (messages sent)."""
        return len(self.agent_messages)

    def to_string(self) -> str:
        """Format transcript for LLM judge evaluation."""
        lines = [
            "# Conversation Transcript",
            f"Persona: {self.persona_name}",
            f"Target: {self.target_url}",
            f"Turns: {self.turn_count}",
            "---",
            "",
        ]
        for entry in self.entries:
            lines.append(str(entry))
            lines.append("")  # Blank line between messages

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize for JSON storage."""
        return {
            "persona_name": self.persona_name,
            "target_url": self.target_url,
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "turn_count": self.turn_count,
            "entries": [
                {
                    "speaker": e.speaker.value,
                    "message": e.message,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in self.entries
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationTranscript":
        """Deserialize from JSON."""
        transcript = cls(
            persona_name=data.get("persona_name", ""),
            target_url=data.get("target_url", ""),
            session_id=data.get("session_id", ""),
        )

        for entry_data in data.get("entries", []):
            entry = TranscriptEntry(
                speaker=Speaker(entry_data["speaker"]),
                message=entry_data["message"],
                timestamp=datetime.fromisoformat(entry_data["timestamp"]),
            )
            transcript.entries.append(entry)

        return transcript


# JavaScript for extracting chat messages from the Expert Council UI
EXTRACT_CHAT_JS = """
() => {
    const messages = [];

    // User messages (agent's messages)
    document.querySelectorAll('[data-testid="user-message"]').forEach(el => {
        messages.push({
            role: 'agent',
            text: el.innerText.trim(),
            order: parseInt(el.dataset.order || '0', 10)
        });
    });

    // System messages (Thinking Partner responses)
    document.querySelectorAll('[data-testid="system-message"]').forEach(el => {
        messages.push({
            role: 'system',
            text: el.innerText.trim(),
            order: parseInt(el.dataset.order || '0', 10)
        });
    });

    // Sort by order to maintain conversation sequence
    messages.sort((a, b) => a.order - b.order);

    return messages;
}
"""

EXTRACT_LAST_SYSTEM_MESSAGE_JS = """
() => {
    const systemMessages = document.querySelectorAll('[data-testid="system-message"]');
    if (systemMessages.length === 0) return null;

    const lastMessage = systemMessages[systemMessages.length - 1];
    return lastMessage.innerText.trim();
}
"""

WAIT_FOR_RESPONSE_JS = """
() => {
    // Check if streaming/thinking indicator is gone
    const streaming = document.querySelector('[data-testid="streaming-indicator"]');
    const thinking = document.querySelector('[data-testid="thinking-indicator"]');

    return !streaming && !thinking;
}
"""
