class SecondBrainError(Exception):
    pass


class NotFoundError(SecondBrainError):
    pass


class ValidationError(SecondBrainError):
    pass


class ConflictError(SecondBrainError):
    pass


class AuthenticationError(SecondBrainError):
    pass


class ProcessingError(SecondBrainError):
    pass


class ProviderError(SecondBrainError):
    pass


class NoteNotFoundError(NotFoundError):
    pass


class NoteAlreadyExistsError(ConflictError):
    pass


class InvalidNoteError(ValidationError):
    pass


class UserAlreadyExistsError(ConflictError):
    pass


class InvalidCredentialsError(AuthenticationError):
    pass


class InvalidRegistrationError(ValidationError):
    pass


class DocumentNotFoundError(NotFoundError):
    pass


class UnsupportedFileTypeError(ValidationError):
    pass


class FileTooLargeError(ValidationError):
    pass


class StorageError(ProcessingError):
    pass


class CorruptedDocumentError(ProcessingError):
    pass


class EncryptedDocumentError(ProcessingError):
    pass


class EmptyDocumentError(ProcessingError):
    pass


class ConversationNotFoundError(NotFoundError):
    pass


class EmbeddingProviderError(ProviderError):
    pass


class LLMProviderError(ProviderError):
    pass
