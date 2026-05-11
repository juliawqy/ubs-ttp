"""
PII redaction for recruitment — delegates to shared.document_parser.
No duplicate logic here.
"""
from shared.document_parser import PIIRedactor

# Re-export for use within the recruitment service
__all__ = ["PIIRedactor"]
