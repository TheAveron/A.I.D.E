from datetime import datetime, timezone


def utcnow() -> datetime:
    """The current UTC time as a naive datetime.

    The database stores naive UTC datetimes (see schemas.base.UTCDatetime);
    this is what the deprecated `datetime.utcnow()` returned.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
