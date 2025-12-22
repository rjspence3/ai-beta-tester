"""Action model for tracking agent interactions."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ActionType(Enum):
    """Types of actions an agent can take."""

    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    SCREENSHOT = "screenshot"
    WAIT = "wait"
    HOVER = "hover"
    SELECT = "select"
    PRESS_KEY = "press_key"


class ActionResult(Enum):
    """Result of an action."""

    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class Action:
    """A single action taken by an agent."""

    sequence: int
    action_type: ActionType
    parameters: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    result: ActionResult = field(default=ActionResult.SUCCESS)
    screenshot_path: str | None = None
    observation: str | None = None
    error_message: str | None = None

    def to_reproduction_step(self) -> str:
        """Convert action to a human-readable reproduction step."""
        match self.action_type:
            case ActionType.NAVIGATE:
                return f"Navigate to {self.parameters.get('url', 'unknown URL')}"
            case ActionType.CLICK:
                element = self.parameters.get("element", "unknown element")
                return f"Click on {element}"
            case ActionType.TYPE:
                element = self.parameters.get("element", "unknown field")
                text = self.parameters.get("text", "")
                return f"Type '{text}' into {element}"
            case ActionType.SCROLL:
                direction = self.parameters.get("direction", "down")
                return f"Scroll {direction}"
            case ActionType.HOVER:
                element = self.parameters.get("element", "unknown element")
                return f"Hover over {element}"
            case ActionType.PRESS_KEY:
                key = self.parameters.get("key", "unknown key")
                return f"Press {key} key"
            case ActionType.SELECT:
                element = self.parameters.get("element", "unknown element")
                value = self.parameters.get("value", "unknown value")
                return f"Select '{value}' from {element}"
            case ActionType.WAIT:
                return f"Wait for {self.parameters.get('condition', 'page load')}"
            case ActionType.SCREENSHOT:
                return "Take screenshot"
            case _:
                return f"Perform {self.action_type.value}"
