
from secondbrain.logging_config import configure_logging
configure_logging()

from secondbrain.exceptions import (
    InvalidNoteError,
    NoteAlreadyExistsError,
    NoteNotFoundError,
)
from secondbrain.repositories.in_memory_note_repository import (
    InMemoryNoteRepository,
)
from secondbrain.services.note_service import NoteService

repository = InMemoryNoteRepository()
service = NoteService(repository)



note = service.create_note(
    1,
    "Python Generators",
    "Generators allow lazy evaluation.",
    user_id=1,
)

print(note)

try:
    service.create_note(
        1,
        "Another Note",
        "This should fail.",
        user_id=1,
    )
except NoteAlreadyExistsError as error:
    print(f"ERROR: {error}")

try:
    service.create_note(
        2,
        "",
        "Some content",
        user_id=1,
    )
except InvalidNoteError as error:
    print(f"ERROR: {error}")

try:
    service.get_note(999, user_id=1)
except NoteNotFoundError as error:
    print(f"ERROR: {error}")
