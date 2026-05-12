"""
Unit tests for PIIRedactor.
Run: pytest services/recruitment/tests/unit/test_pii_redaction.py -v
"""

import pytest
from shared.document_parser.pii_redactor import PIIRedactor


@pytest.fixture
def redactor():
    return PIIRedactor()


class TestEmailRedaction:
    def test_single_email_is_redacted(self, redactor):
        text, replacements = redactor.redact("Contact me at julia.wong@ubs.com for details.")
        assert "julia.wong@ubs.com" not in text
        assert "[EMAIL_0]" in text

    def test_email_stored_in_replacements_map(self, redactor):
        _, replacements = redactor.redact("Email: julia.wong@ubs.com")
        assert replacements["[EMAIL_0]"] == "julia.wong@ubs.com"

    def test_multiple_emails_numbered_separately(self, redactor):
        text, replacements = redactor.redact("From: a@b.com, cc: c@d.com")
        assert "[EMAIL_0]" in text
        assert "[EMAIL_1]" in text
        assert len([k for k in replacements if k.startswith("[EMAIL")]) == 2


class TestPhoneRedaction:
    def test_uk_phone_is_redacted(self, redactor):
        text, _ = redactor.redact("Call me on +44 7911 123456.")
        assert "+44 7911 123456" not in text

    def test_sg_phone_is_redacted(self, redactor):
        text, _ = redactor.redact("Mobile: +65 9123 4567")
        assert "+65 9123 4567" not in text

    def test_phone_stored_in_replacements_map(self, redactor):
        _, replacements = redactor.redact("Tel: +65 9123 4567")
        assert any("9123" in v for v in replacements.values())


class TestURLRedaction:
    def test_https_url_is_redacted(self, redactor):
        text, _ = redactor.redact("Portfolio: https://juliawong.dev/work")
        assert "https://juliawong.dev/work" not in text

    def test_www_url_is_redacted(self, redactor):
        text, _ = redactor.redact("See www.linkedin.com/in/juliawong")
        assert "www.linkedin.com/in/juliawong" not in text


class TestGraduationYearRedaction:
    def test_graduation_year_is_redacted(self, redactor):
        text, _ = redactor.redact("Graduated NUS in 2019.")
        assert "2019" not in text

    def test_old_year_is_redacted(self, redactor):
        text, _ = redactor.redact("Started career in 1998.")
        assert "1998" not in text


class TestCleanText:
    def test_clean_text_passes_through_unchanged(self, redactor):
        clean = "Experienced software engineer with 5 years in Python."
        text, replacements = redactor.redact(clean)
        assert text == clean
        assert replacements == {}

    def test_empty_string_returns_empty(self, redactor):
        text, replacements = redactor.redact("")
        assert text == ""
        assert replacements == {}


class TestCombined:
    def test_full_cv_header_is_fully_redacted(self, redactor):
        cv_header = (
            "Julia Wong\n"
            "julia.wong@gmail.com | +65 9123 4567 | www.juliawong.dev\n"
            "Graduated 2022, National University of Singapore\n"
        )
        text, replacements = redactor.redact(cv_header)
        assert "julia.wong@gmail.com" not in text
        assert "+65 9123 4567" not in text
        assert "www.juliawong.dev" not in text
        assert "2022" not in text
        assert len(replacements) >= 4