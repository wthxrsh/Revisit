from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from secondbrain.models.note import Note
from secondbrain.repositories.base import NoteRepository
from secondbrain.database.models import NoteModel


class PostgresNoteRepository(NoteRepository):

    def __init__(self, session: Session):
        self.session = session

    def save(self, note: Note, user_id: int) -> Note:
        model = NoteModel(
            id=note.id,
            user_id=user_id,
            title=note.title,
            content=note.content,
            created_at=note.created_at,
            updated_at=note.updated_at,
        )

        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)

        return self._to_domain(model)

    def get_by_id(self, note_id: int, user_id: int) -> Note | None:
        statement = select(NoteModel).where(
            NoteModel.id == note_id,
            NoteModel.user_id == user_id,
        )

        model = self.session.scalar(statement)

        if model is None:
            return None

        return self._to_domain(model)

    def get_all(
            self,
            user_id: int,
            limit: int = 20,
            offset: int = 0,
            search: str | None = None,
    ) -> list[Note]:
        statement = select(NoteModel).where(
            NoteModel.user_id == user_id,
        )

        if search:
            search_pattern = f"%{search}%"
            statement = statement.where(
                or_(
                    NoteModel.title.ilike(search_pattern),
                    NoteModel.content.ilike(search_pattern),
                )
            )

        statement = (
            statement
            .order_by(NoteModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        models = self.session.scalars(statement).all()

        return [self._to_domain(model) for model in models]


    def delete(self, note_id: int, user_id: int) -> bool:
        statement = select(NoteModel).where(
            NoteModel.id == note_id,
            NoteModel.user_id == user_id,
        )
        model = self.session.scalar(statement)

        if model is None:
            return False

        self.session.delete(model)
        self.session.commit()

        return True

    @staticmethod
    def _to_domain(model: NoteModel) -> Note:
        return Note(
            id=model.id,
            title=model.title,
            content=model.content,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def update(self, note: Note, user_id: int) -> Note | None:
        statement = select(NoteModel).where(
            NoteModel.id == note.id,
            NoteModel.user_id == user_id,
        )
        model = self.session.scalar(statement)

        if model is None:
            return None

        model.title = note.title
        model.content = note.content
        model.updated_at = note.updated_at

        self.session.commit()
        self.session.refresh(model)

        return self._to_domain(model)