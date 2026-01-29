"""DSPy LM adapter that uses Claude Code's infrastructure.

This allows DSPy's prompt optimization framework to use the same
Claude session as the rest of the codebase, without requiring
a separate API key.
"""

import asyncio
import concurrent.futures
import threading
from typing import Any

import dspy
from dspy.clients.lm import LM

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    AssistantMessage,
    ResultMessage,
    TextBlock,
)


def _run_async_in_new_loop(coro):
    """Run an async coroutine in a new event loop on a separate thread.

    This handles the case where we're already inside an async context
    (e.g., called from the orchestrator's async methods).
    """
    result = None
    exception = None

    def run():
        nonlocal result, exception
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(coro)
            finally:
                loop.close()
        except Exception as e:
            exception = e

    thread = threading.Thread(target=run)
    thread.start()
    thread.join()

    if exception:
        raise exception
    return result


class ClaudeCodeLM(LM):
    """DSPy Language Model that uses Claude Code's ClaudeSDKClient.

    This adapter allows DSPy to use the same Claude infrastructure
    as the rest of the ai_beta_tester codebase.

    Usage:
        lm = ClaudeCodeLM(model="sonnet")
        dspy.configure(lm=lm)

        # Now DSPy modules will use Claude Code
        module = dspy.ChainOfThought(MySignature)
        result = module(input="...")
    """

    def __init__(
        self,
        model: str = "sonnet",
        max_tokens: int = 4096,
        temperature: float | None = None,
        **kwargs,
    ):
        """Initialize the Claude Code LM adapter.

        Args:
            model: Claude model to use ("sonnet", "opus", "haiku")
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (None = model default)
        """
        # Store Claude model separately (super().__init__ overwrites self.model)
        self._claude_model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.kwargs = kwargs

        # Track usage for DSPy's history
        self.history = []

        # Required by DSPy LM base class
        super().__init__(model=f"claude-code/{model}", model_type="chat")

    def __call__(
        self,
        prompt: str | None = None,
        messages: list[dict] | None = None,
        **kwargs,
    ) -> list[dict]:
        """Execute a prompt using Claude Code.

        Args:
            prompt: Simple string prompt (legacy DSPy interface)
            messages: Chat messages format [{"role": "user", "content": "..."}]
            **kwargs: Additional arguments (temperature, max_tokens, etc.)

        Returns:
            List of response dicts with 'text' key (DSPy format)
        """
        # Handle both prompt and messages formats
        if messages:
            # Convert messages to a single prompt
            formatted_prompt = self._format_messages(messages)
        elif prompt:
            formatted_prompt = prompt
        else:
            raise ValueError("Either prompt or messages must be provided")

        # Run async call - use thread-based approach to handle nested event loops
        response_text = _run_async_in_new_loop(self._call_async(formatted_prompt, **kwargs))

        # Track in history for DSPy
        self.history.append({
            "prompt": formatted_prompt,
            "response": response_text,
            "kwargs": kwargs,
        })

        # Return in DSPy's expected format
        return [{"text": response_text}]

    async def _call_async(self, prompt: str, **kwargs) -> str:
        """Make the actual async call to Claude Code."""

        # Merge instance defaults with call-specific kwargs
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        options = ClaudeAgentOptions(
            model=self._claude_model,
            max_turns=1,
            permission_mode="bypassPermissions",
        )

        response_text = ""

        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)

                async for message in client.receive_messages():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                response_text += block.text
                    if isinstance(message, ResultMessage):
                        break

        except Exception as e:
            response_text = f"Error: {e}"

        return response_text

    def _format_messages(self, messages: list[dict]) -> str:
        """Format chat messages into a single prompt string."""
        parts = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                parts.append(f"System: {content}")
            elif role == "user":
                parts.append(f"User: {content}")
            elif role == "assistant":
                parts.append(f"Assistant: {content}")
            else:
                parts.append(content)

        return "\n\n".join(parts)

    def basic_request(self, prompt: str, **kwargs) -> str:
        """Basic request method required by DSPy LM interface."""
        results = self(prompt=prompt, **kwargs)
        return results[0]["text"] if results else ""

    def inspect_history(self, n: int = 1) -> list[dict]:
        """Return the last n items from history."""
        return self.history[-n:] if self.history else []


def configure_dspy_with_claude_code(model: str = "sonnet"):
    """Configure DSPy to use Claude Code as the LM backend.

    Args:
        model: Claude model to use ("sonnet", "opus", "haiku")

    Example:
        from ai_beta_tester.experiments.dspy_persona.claude_code_lm import configure_dspy_with_claude_code

        configure_dspy_with_claude_code(model="sonnet")

        # Now all DSPy operations use Claude Code
        class MySignature(dspy.Signature):
            input: str = dspy.InputField()
            output: str = dspy.OutputField()

        module = dspy.ChainOfThought(MySignature)
        result = module(input="Hello")
    """
    lm = ClaudeCodeLM(model=model)
    dspy.configure(lm=lm)
    return lm
