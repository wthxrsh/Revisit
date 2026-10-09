"""Regenerate the binary PDF fixtures used by the test suite.

Run from the project root:

    python tests/fixtures/generate_fixtures.py

Requires the optional ``dev`` extra (reportlab). The generated files are
committed to the repository so the test suite itself does not need reportlab.
"""

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

FIXTURES = Path(__file__).parent


def _text_pdf() -> Path:
    path = FIXTURES / "sample.pdf"
    pdf = canvas.Canvas(str(path), pagesize=letter)

    pdf.drawString(
        72,
        720,
        "SecondBrain is a personal knowledge management system.",
    )
    pdf.drawString(
        72,
        700,
        "It lets users store notes and upload PDF documents.",
    )
    pdf.showPage()

    pdf.drawString(
        72,
        720,
        "Retrieval augmented generation combines search with a language model.",
    )
    pdf.drawString(
        72,
        700,
        "Chunking splits documents into smaller passages before embedding.",
    )
    pdf.showPage()

    pdf.save()
    return path


def _empty_pdf() -> Path:
    path = FIXTURES / "empty.pdf"
    pdf = canvas.Canvas(str(path), pagesize=letter)
    pdf.showPage()
    pdf.save()
    return path


def _encrypted_pdf() -> Path:
    from reportlab.lib import pdfencrypt

    path = FIXTURES / "encrypted.pdf"
    encrypt = pdfencrypt.StandardEncryption(
        userPassword="secret",
        ownerPassword="secret",
        canPrint=1,
    )
    pdf = canvas.Canvas(str(path), pagesize=letter, encrypt=encrypt)
    pdf.drawString(72, 720, "This content is protected.")
    pdf.showPage()
    pdf.save()
    return path


if __name__ == "__main__":
    for created in (_text_pdf(), _empty_pdf(), _encrypted_pdf()):
        print(f"wrote {created}")
