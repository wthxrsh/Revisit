import logging
import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError
from pypdf.errors import PyPdfError

from secondbrain.exceptions import (
    CorruptedDocumentError,
    EmptyDocumentError,
    EncryptedDocumentError,
)

logger = logging.getLogger(__name__)

_WHITESPACE = re.compile(r"\s+")


@dataclass
class PageText:
    page_number: int
    text: str


class PdfTextExtractor:

    def extract(self, path: str | Path) -> list[PageText]:
        try:
            reader = PdfReader(str(path))
        except (PdfReadError, PyPdfError, OSError, ValueError) as error:
            logger.warning("Failed to open PDF: %s", type(error).__name__)
            raise CorruptedDocumentError(
                "The file is not a valid or readable PDF"
            ) from error

        if reader.is_encrypted:
            self._decrypt(reader)

        pages: list[PageText] = []

        for index, page in enumerate(reader.pages, start=1):
            try:
                raw_text = page.extract_text() or ""
            except Exception as error:  # parser boundary: any failure -> domain error
                logger.warning(
                    "Failed to extract page %s: %s",
                    index,
                    type(error).__name__,
                )
                raise CorruptedDocumentError(
                    f"Failed to extract text from page {index}"
                ) from error

            pages.append(
                PageText(
                    page_number=index,
                    text=_normalize(raw_text),
                )
            )

        if not any(page.text for page in pages):
            raise EmptyDocumentError(
                "No extractable text found. The PDF may be scanned images "
                "without OCR."
            )

        return pages

    @staticmethod
    def _decrypt(reader: PdfReader) -> None:
        try:
            result = reader.decrypt("")
        except Exception as error:  # pypdf raises several crypto errors
            raise EncryptedDocumentError(
                "The PDF is encrypted and cannot be read"
            ) from error

        if not result:
            raise EncryptedDocumentError(
                "The PDF is password-protected and cannot be read"
            )


def _normalize(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()
