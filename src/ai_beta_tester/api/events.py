"""Server-Sent Events (SSE) event publisher for real-time updates."""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import AsyncGenerator
from uuid import UUID


class EventType(str, Enum):
    """Types of events that can be published."""
    SESSION_STARTED = "session_started"
    AGENT_STARTED = "agent_started"
    ACTION_TAKEN = "action_taken"
    FINDING_REPORTED = "finding_reported"
    AGENT_COMPLETED = "agent_completed"
    SESSION_COMPLETED = "session_completed"
    ERROR = "error"


@dataclass
class Event:
    """A single event to be published."""
    event_type: EventType
    data: dict
    timestamp: datetime = field(default_factory=datetime.now)

    def to_sse(self) -> str:
        """Format event for SSE transmission."""
        payload = {
            "type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            **self.data,
        }
        return f"data: {json.dumps(payload)}\n\n"


class EventPublisher:
    """Manages event publishing for a single session."""

    def __init__(self, session_id: UUID):
        self.session_id = session_id
        self.queue: asyncio.Queue[Event | None] = asyncio.Queue()
        self._closed = False

    async def publish(self, event_type: EventType, data: dict) -> None:
        """Publish an event to all subscribers."""
        if self._closed:
            return
        event = Event(event_type=event_type, data=data)
        await self.queue.put(event)

    async def subscribe(self) -> AsyncGenerator[str, None]:
        """Subscribe to events for this session.

        Yields SSE-formatted event strings.
        """
        while not self._closed:
            try:
                event = await asyncio.wait_for(self.queue.get(), timeout=30.0)
                if event is None:
                    break
                yield event.to_sse()
            except asyncio.TimeoutError:
                # Send keepalive
                yield ": keepalive\n\n"

    async def close(self) -> None:
        """Close the publisher and notify subscribers."""
        self._closed = True
        await self.queue.put(None)


class EventManager:
    """Manages event publishers for all active sessions."""

    def __init__(self):
        self._publishers: dict[UUID, EventPublisher] = {}

    def create_publisher(self, session_id: UUID) -> EventPublisher:
        """Create a new event publisher for a session."""
        publisher = EventPublisher(session_id)
        self._publishers[session_id] = publisher
        return publisher

    def get_publisher(self, session_id: UUID) -> EventPublisher | None:
        """Get the event publisher for a session."""
        return self._publishers.get(session_id)

    async def close_publisher(self, session_id: UUID) -> None:
        """Close and remove a session's event publisher."""
        publisher = self._publishers.pop(session_id, None)
        if publisher:
            await publisher.close()


# Global event manager instance
event_manager = EventManager()
