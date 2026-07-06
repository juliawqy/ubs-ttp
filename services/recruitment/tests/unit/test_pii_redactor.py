"""
Unit tests for PIIRedactor.
The key invariant: a candidate's name must not survive into the
bias-sensitive resume review that hiring managers see.
"""
import pytest
from shared.document_parser.pii_redactor import PIIRedactor, DEFAULT_PII_PATTERNS


@pytest.fixture
def redactor():
    return PIIRedactor()


class TestNameRedaction:
    def test_titled_name_is_redacted(self, redactor):
        text = "Dr. Jane Smith has 10 years of experience."
        redacted, _ = redactor.redact(text)
        assert "Jane Smith" not in redacted
        assert "Dr." not in redacted or "[NAME_TITLED" in redacted

    def test_mr_prefix_name_is_redacted(self, redactor):
        text = "Applicant: Mr. John Doe. Skills: Python, SQL."
        redacted, _ = redactor.redact(text)
        assert "John Doe" not in redacted

    def test_ms_prefix_name_is_redacted(self, redactor):
        text = "Ms. Alice Wong graduated from NUS."
        redacted, _ = redactor.redact(text)
        assert "Alice Wong" not in redacted

    def test_label_prefixed_name_is_redacted(self, redactor):
        cv = "Name: Sarah Lee\nEmail: sarah@example.com\nSkills: Python"
        redacted, _ = redactor.redact(cv)
        assert "Sarah Lee" not in redacted

    def test_full_name_label_is_redacted(self, redactor):
        cv = "Full Name: James Carter\nPhone: +65 9123 4567"
        redacted, _ = redactor.redact(cv)
        assert "James Carter" not in redacted

    def test_replacement_map_contains_original_name(self, redactor):
        text = "Dr. Jane Smith applies for the role."
        _, replacements = redactor.redact(text)
        assert any("Jane Smith" in v for v in replacements.values())

    def test_redacted_text_contains_placeholder_token(self, redactor):
        text = "Mr. Ali Hassan is a senior engineer."
        redacted, _ = redactor.redact(text)
        assert "[NAME_TITLED" in redacted


class TestEmailRedaction:
    def test_email_is_redacted(self, redactor):
        text = "Contact me at jane.smith@gmail.com for more info."
        redacted, _ = redactor.redact(text)
        assert "jane.smith@gmail.com" not in redacted
        assert "[EMAIL" in redacted


class TestPhoneRedaction:
    def test_phone_number_is_redacted(self, redactor):
        text = "Call me on +65 9123 4567."
        redacted, _ = redactor.redact(text)
        assert "9123 4567" not in redacted


class TestURLRedaction:
    def test_url_is_redacted(self, redactor):
        text = "Portfolio: https://github.com/janesmith"
        redacted, _ = redactor.redact(text)
        assert "github.com/janesmith" not in redacted


class TestFullCVRedaction:
    """Ensures a realistic CV strips all identity before a manager sees it."""

    def test_cv_with_all_pii_types_redacted(self, redactor):
        cv = (
            "Name: Maria Tan\n"
            "Email: maria.tan@email.com\n"
            "Phone: +65 8765 4321\n"
            "LinkedIn: https://linkedin.com/in/mariatan\n"
            "Class of 2019\n\n"
            "Ms. Maria Tan has led cross-functional teams at three companies."
        )
        redacted, replacements = redactor.redact(cv)
        assert "Maria Tan"             not in redacted
        assert "maria.tan@email.com"   not in redacted
        assert "8765 4321"             not in redacted
        assert "linkedin.com/in/mariatan" not in redacted
        # Original values are stored in the replacement map, not the text
        assert any("Maria Tan" in v or "maria.tan" in v for v in replacements.values())

    def test_redacted_cv_retains_skill_content(self, redactor):
        cv = "Name: Bob Lee\nSkills: Python, FastAPI, PostgreSQL\nYears of experience: 8"
        redacted, _ = redactor.redact(cv)
        assert "Python" in redacted
        assert "FastAPI" in redacted
        assert "PostgreSQL" in redacted
