import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from secondbrain.exceptions import (
    FileTooLargeError,
    StorageError,
    UnsupportedFileTypeError,
)

logger = logging.getLogger(__name__)

PDF_MAGIC = b"%PDF-"
READ_CHUNK_SIZE = 1024 * 1024


@dataclass
class StoredFile:
    storage_key: str
    size: int
    content_type: str


class LocalFileStorage:

    def __init__(self, base_path: str | Path, max_size_bytes: int):
        self.base_path = Path(base_path).expanduser().resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_bytes

    def _resolve(self, storage_key: str) -> Path:
        candidate = (self.base_path / storage_key).resolve()
        base = str(self.base_path)
        candidate_str = str(candidate)
        if candidate != self.base_path and not candidate_str.startswith(
            base + os.sep
        ):
            raise StorageError("Invalid storage key")
        return candidate

    def save_stream(self, fileobj: BinaryIO) -> StoredFile:
        header = fileobj.read(len(PDF_MAGIC))

        if header != PDF_MAGIC:
            raise UnsupportedFileTypeError(
                "Only PDF files are supported"
            )

        storage_key = f"{uuid4().hex}.pdf"
        target = self._resolve(storage_key)
        target.parent.mkdir(parents=True, exist_ok=True)

        size = len(header)

        try:
            with target.open("wb") as destination:
                destination.write(header)

                while True:
                    chunk = fileobj.read(READ_CHUNK_SIZE)
                    if not chunk:
                        break

                    size += len(chunk)
                    if size > self.max_size_bytes:
                        raise FileTooLargeError(
                            f"File exceeds the maximum size of "
                            f"{self.max_size_bytes // (1024 * 1024)} MB"
                        )

                    destination.write(chunk)
        except FileTooLargeError:
            self._remove(target)
            raise
        except OSError as error:
            self._remove(target)
            raise StorageError("Failed to store uploaded file") from error

        return StoredFile(
            storage_key=storage_key,
            size=size,
            content_type="application/pdf",
        )

    def path_for(self, storage_key: str) -> Path:
        return self._resolve(storage_key)

    def delete(self, storage_key: str) -> None:
        try:
            path = self._resolve(storage_key)
        except StorageError:
            logger.warning("Refused to delete suspicious storage key")
            return

        self._remove(path)

    @staticmethod
    def _remove(path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Could not remove file at %s", path)
