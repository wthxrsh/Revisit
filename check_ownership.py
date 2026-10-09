
from secondbrain.models.note import Note
from secondbrain.repositories.in_memory_note_repository import (
    InMemoryNoteRepository,
)

repository = InMemoryNoteRepository()

note = Note(
    id=1,
    title="Private note",
    content="Only user 1 should access this.",
)

repository.save(note, user_id=1)

# The owner can read the note.
assert repository.get_by_id(1, user_id=1) is not None

# Another user cannot read, update, or delete it.
assert repository.get_by_id(1, user_id=2) is None

other_user_note = Note(
    id=1,
    title="Modified by user 2",
    content="This must not be saved.",
)
assert repository.update(other_user_note, user_id=2) is None
assert repository.delete(1, user_id=2) is False

# The original note remains unchanged.
saved_note = repository.get_by_id(1, user_id=1)
assert saved_note is not None
assert saved_note.title == "Private note"

print("Ownership checks passed.")
