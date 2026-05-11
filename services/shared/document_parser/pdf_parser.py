"""
PDF and Word document parser.
Uses pdfplumber (not AWS Textract) — no AI cost, no vendor lock-in.
"""
import pdfplumber


class PDFParser:
    """
    Parses text content from PDF and Word documents.
    Single responsibility: extract raw text. Does not analyse or redact.
    """

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract all text from a PDF file."""
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()

    def extract_text_from_bytes(self, file_bytes: bytes) -> str:
        """Extract text from PDF provided as raw bytes (e.g. from S3)."""
        import io
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
