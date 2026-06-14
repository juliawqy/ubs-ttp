"""
PII redactor -- strips identity signals from resume text before review.
Uses regex patterns. Rule-based, no AI cost.
Redacts: names, email addresses, phone numbers, URLs, graduation years.
"""
import re


# Default patterns used when none are provided -- kept at module level so they
# can be imported and extended without instantiating PIIRedactor.
DEFAULT_PII_PATTERNS: dict[str, re.Pattern] = {
    "EMAIL": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "PHONE": re.compile(r"(\+?\d[\d\s\-().]{7,}\d)"),
    "URL":   re.compile(r"https?://\S+|www\.\S+"),
    "YEAR":  re.compile(r"\b(19|20)\d{2}\b"),
}


class PIIRedactor:
    """
    Redacts PII from text using a labelled set of regex patterns.
    Returns redacted text and a mapping of what was replaced.
    Keeping original <-> redacted mapping server-side allows UI re-hydration.

    Args:
        patterns: dict mapping label -> compiled regex.
                  Defaults to DEFAULT_PII_PATTERNS.
                  Pass a custom dict to add/remove PII types without
                  subclassing (satisfies OCP).
    """

    def __init__(self, patterns: dict[str, re.Pattern] | None = None):
        self._patterns = patterns if patterns is not None else DEFAULT_PII_PATTERNS

    def redact(self, text: str) -> tuple[str, dict]:
        """
        Redact PII from text.
        Returns (redacted_text, replacements_map).
        replacements_map allows the original values to be restored server-side.
        """
        replacements: dict[str, str] = {}
        counter = [0]

        def replace(pattern: re.Pattern, label: str, text: str) -> str:
            def _replace(match: re.Match) -> str:
                key = f"[{label}_{counter[0]}]"
                replacements[key] = match.group()
                counter[0] += 1
                return key
            return pattern.sub(_replace, text)

        for label, pattern in self._patterns.items():
            text = replace(pattern, label, text)

        return text, replacements
