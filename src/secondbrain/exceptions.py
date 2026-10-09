class NoteNotFoundError(Exception):
    pass


class NoteAlreadyExistsError(Exception):
    pass


class InvalidNoteError(Exception):
    pass

class UserAlreadyExistsError(Exception):
    pass

class InvalidCredentialsError(Exception):
    pass