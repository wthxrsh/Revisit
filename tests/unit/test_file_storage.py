import io

import pytest

from secondbrain.exceptions import (
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from secondbrain.storage.file_storage import LocalFileStorage

VALID_PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF"


def test_saves_valid_pdf(tmp_path):
    storage = LocalFileStorage(tmp_path, max_size_bytes=10_000)

    stored = storage.save_stream(io.BytesIO(VALID_PDF))

    assert stored.storage_key.endswith(".pdf")
    assert stored.size == len(VALID_PDF)
    assert storage.path_for(stored.storage_key).exists()


def test_rejects_non_pdf(tmp_path):
    storage = LocalFileStorage(tmp_path, max_size_bytes=10_000)

    with pytest.raises(UnsupportedFileTypeError):
        storage.save_stream(io.BytesIO(b"not a pdf at all"))


def test_rejects_oversized_file(tmp_path):
    storage = LocalFileStorage(tmp_path, max_size_bytes=10)

    with pytest.raises(FileTooLargeError):
        storage.save_stream(io.BytesIO(VALID_PDF))


def test_oversized_file_leaves_no_partial_file(tmp_path):
    storage = LocalFileStorage(tmp_path, max_size_bytes=10)

    with pytest.raises(FileTooLargeError):
        storage.save_stream(io.BytesIO(VALID_PDF))

    assert list(tmp_path.iterdir()) == []


def test_generated_keys_are_unique(tmp_path):
    storage = LocalFileStorage(tmp_path, max_size_bytes=10_000)

    first = storage.save_stream(io.BytesIO(VALID_PDF))
    second = storage.save_stream(io.BytesIO(VALID_PDF))

    assert first.storage_key != second.storage_key


def test_delete_removes_file(tmp_path):
    storage = LocalFileStorage(tmp_path, max_size_bytes=10_000)
    stored = storage.save_stream(io.BytesIO(VALID_PDF))

    storage.delete(stored.storage_key)

    assert not storage.path_for(stored.storage_key).exists()


def test_delete_rejects_path_traversal(tmp_path):
    storage = LocalFileStorage(tmp_path, max_size_bytes=10_000)

    outside = tmp_path.parent / "outside.txt"
    outside.write_text("do not delete me")

    storage.delete("../outside.txt")

    assert outside.exists()
