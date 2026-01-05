"""Tools for Analytical personalities (Privacy, Manager, Auditor)."""

class PrivacyTools:
    @staticmethod
    def get_cookie_inspector_js() -> str:
        return """
// HELPER: Cookie & Storage Inspector
(function() {
    const cookies = document.cookie;
    const local = JSON.stringify(localStorage);
    const session = JSON.stringify(sessionStorage);
    console.log("[Privacy Scan] Cookies: " + cookies.substring(0, 500));
    console.log("[Privacy Scan] LocalStorage keys: " + Object.keys(localStorage).join(", "));
    return `Analysis Complete. Found ${cookies.split(';').length} cookies, ${Object.keys(localStorage).length} local storage items.`;
})();
"""

    @staticmethod
    def get_pii_scanner_js() -> str:
        return """
// HELPER: PII Scanner
(function() {
    const body = document.body.innerText;
    const emailRegex = /[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,6}/g;
    const phoneRegex = /\\+?[0-9]{10,14}/g;
    const emails = body.match(emailRegex) || [];
    const phones = body.match(phoneRegex) || [];
    return `PII Scan Results: Found ${emails.length} emails, ${phones.length} phone numbers visible.`;
})();
"""

class ManagerTools:
    @staticmethod
    def get_cta_analyzer_js() -> str:
        return """
// HELPER: CTA Prominence Analyzer
(function() {
    const buttons = Array.from(document.querySelectorAll('button, a.btn, input[type="submit"]'));
    const scored = buttons.map(b => {
        const rect = b.getBoundingClientRect();
        const area = rect.width * rect.height;
        const style = window.getComputedStyle(b);
        const color = style.backgroundColor;
        // Simple heuristic: area * contrast (assumed high for colored buttons)
        return { text: b.innerText, score: area, color: color };
    });
    scored.sort((a, b) => b.score - a.score);
    return JSON.stringify(scored.slice(0, 3), null, 2);
})();
"""

class AuditorTools:
    @staticmethod
    def get_code_audit_prompt() -> str:
        return """
## Code Audit Strategy
You have filesystem access. Don't guess.
1. **List Files**: `list_directory(".")` to see the structure.
2. **Find Handlers**: If you see a "Submit" button, search for its handler in the code using `search_files("Submit")` or `search_files("function handleSubmit")`.
3. **Verify Validation**: Read the backend code to see if inputs are actually validated.
4. **Check Secrets**: Search for "API_KEY", "secret", "password" in the codebase.
"""
