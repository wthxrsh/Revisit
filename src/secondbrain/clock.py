from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current UTC time as a naive datetime.

    The database columns are timezone-naive, so we strip the tzinfo to keep
    application and storage representations consistent.
    """
    return datetime.now(UTC).replace(tzinfo=None)
