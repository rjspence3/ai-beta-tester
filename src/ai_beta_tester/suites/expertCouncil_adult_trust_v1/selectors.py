"""Stable data-testid selectors for expertCouncil (Thinking Partner).

These selectors are assumed to be stable in the target application.
The trust test suite uses these to verify end states and UI behaviors.

Testing Mode:
    Append ?bypass=test to the URL to skip authentication in development:
    - http://expert-council.test/app?bypass=test

Payment Testing:
    To test payment flows without real Stripe, append query params to the URL:
    - Success: /?checkout=success  -> triggers payment-success element
    - Failure: /?checkout=failed   -> triggers payment-failure element
    - Canceled: /?checkout=canceled -> triggers payment-failure element
"""

SELECTORS = {
    # Session management
    "new_session_button": "[data-testid='new-session-button']",

    # Initial topic entry (fresh session - TopicInput component)
    "topic_input": "[data-testid='topic-input']",
    "start_council_button": "[data-testid='start-council-button']",

    # In-session chat flow (after council started)
    "chat_container": "[data-testid='chat-container']",
    "chat_input": "[data-testid='chat-input']",
    "send_button": "[data-testid='send-button']",

    # Chat messages (for real API response detection)
    "chat_message": "[data-testid='chat-message']",
    "system_message": "[data-testid='system-message']",
    "user_message": "[data-testid='user-message']",
    "streaming_indicator": "[data-testid='streaming-indicator']",
    "thinking_indicator": "[data-testid='thinking-indicator']",

    # Closure states
    "decision_summary": "[data-testid='decision-summary']",
    "decision_end_state": "[data-testid='decision-end-state']",
    "action_path": "[data-testid='action-path']",
    "deferral_until": "[data-testid='deferral-until']",
    "adjourn_reason": "[data-testid='adjourn-reason']",

    # Economics / Paywall
    "session_credits_remaining": "[data-testid='session-credits-remaining']",
    "paywall_modal": "[data-testid='paywall-modal']",
    "upgrade_button": "[data-testid='upgrade-button']",
    "payment_success": "[data-testid='payment-success']",
    "payment_failure": "[data-testid='payment-failure']",
}


def get_selector(name: str) -> str:
    """Get a selector by name, raising KeyError if not found."""
    if name not in SELECTORS:
        raise KeyError(f"Unknown selector '{name}'. Available: {list(SELECTORS.keys())}")
    return SELECTORS[name]
