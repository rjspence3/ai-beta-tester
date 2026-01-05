"""Tools for the Chaos Gremlin personality."""

import random

_NASTY_INPUTS = [
    "' OR 1=1; --",  # SQL Injection
    "<script>alert('XSS')</script>",  # XSS
    "A" * 1000,  # Buffer Overflow
    "😊" * 100,  # Unicode spam
    "null",  # String literal null
    "undefined",  # String literal undefined
    "NaN",  # String literal NaN
    "../etc/passwd",  # Path traversal
    "javascript:void(0)",  # JS URI
    "\\x00",  # Null byte
]

class ChaosTools:
    @staticmethod
    def get_fuzzing_inputs() -> str:
        """Return a formatted list of nasty inputs for the system prompt."""
        # Return a shuffled subsample
        shuffled = _NASTY_INPUTS[:]
        random.shuffle(shuffled)
        items = "\n".join([f"- `{s}`" for s in shuffled[:5]])
        return f"""
Here is a list of 'nasty' inputs you MUST try entering into forms:
{items}
"""

    @staticmethod
    def get_event_spam_js() -> str:
        """Return a JS snippet for spamming events."""
        return """
// JS Snippet to Click Randomly 10 times
(function() {
    const w = window.innerWidth;
    const h = window.innerHeight;
    for(let i=0; i<10; i++) {
        const x = Math.floor(Math.random() * w);
        const y = Math.floor(Math.random() * h);
        const el = document.elementFromPoint(x, y);
        if(el) el.click();
    }
    return "Clicked 10 random points";
})();
"""
