from secondbrain.models.note import Note
from secondbrain.repositories.base import NoteRepository


class InMemoryNoteRepository(NoteRepository):

    def __init__(self) -> None:
        self.notes: dict[int, tuple[Note, int]] = {}
        self._next_id = 1

    def _assign_id(self) -> int:
        note_id = self._next_id
        self._next_id += 1
        return note_id

    def save(self, note: Note, user_id: int) -> Note:
        if note.id is None:
            note.id = self._assign_id()

        self.notes[note.id] = (note, user_id)
        return note

    def get_by_id(self, note_id: int, user_id: int) -> Note | None:
        entry = self.notes.get(note_id)

        if entry is None:
            return None

        note, owner_id = entry

        if owner_id != user_id:
            return None

        return note

    def get_all(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
    ) -> list[Note]:

        notes = [
            note
            for note, owner_id in self.notes.values()
            if owner_id == user_id
        ]

        if search:
            search_term = search.lower()
            notes = [
                note
                for note in notes
                if search_term in note.title.lower()
                or search_term in note.content.lower()
            ]

        return notes[offset:offset + limit]

    def delete(self, note_id: int, user_id: int) -> bool:
        entry = self.notes.get(note_id)

        if entry is None:
            return False

        _, owner_id = entry

        if owner_id != user_id:
            return False

        del self.notes[note_id]
        return True

    def update(self, note: Note, user_id: int) -> Note | None:
        entry = self.notes.get(note.id)  # type: ignore[index]

        if entry is None:
            return None

        _, owner_id = entry

        if owner_id != user_id:
            return None

        self.notes[note.id] = (note, user_id)  # type: ignore[index]
        return note
