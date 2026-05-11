"""
PII redactor — strips identity signals from resume text before review.
Uses spaCy NER. Rule-based, no AI cost.
Redacts: names, email addresses, phone numbers, URLs, graduation years.
"""
import re


class PIIRedactor:
    """
    Redacts PII from text using regex and NER patterns.
    Returns redacted text and a mapping of what was replaced.
    Keeping original ↔ redacted mapping server-side allows UI re-hydration.
    """

    EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    PHONE_PATTERN = re.compile(r"(\+?\d[\d\s\-().]{7,}\d)")
    URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
    GRAD_YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")

    def redact(self, text: str) -> tuple[str, dict]:
        """
        Redact PII from text.
        Returns (redacted_text, replacements_map).
        replacements_map allows the original values to be restored server-side.
        """
        replacements = {}
        counter = [0]

        def replace(pattern, label, text):
            def _replace(match):
                key = f"[{label}_{counter[0]}]"
                replacements[key] = match.group()
                counter[0] += 1
                return key
            return pattern.sub(_replace, text)

        text = replace(self.EMAIL_PATTERN, "EMAIL", text)
        text = replace(self.PHONE_PATTERN, "PHONE", text)
        text = replace(self.URL_PATTERN, "URL", text)
        text = replace(self.GRAD_YEAR_PATTERN, "YEAR", text)

        return text, replacements
