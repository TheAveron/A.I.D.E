"""Shared building blocks for the Pydantic schemas."""

from datetime import datetime, timezone
from typing import Annotated, ClassVar

from pydantic import AfterValidator, BaseModel, model_validator


def _as_utc(value: datetime) -> datetime:
    """Tag naive datetimes as UTC.

    The database stores naive UTC datetimes (datetime.utcnow). Serialized as
    is, they carry no timezone and browsers read them as *local* time, which
    shifts every date by the viewer's UTC offset.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


UTCDatetime = Annotated[datetime, AfterValidator(_as_utc)]

# Largest value of the INTEGER columns (quantities, totals in circulation).
# A bigger number used to reach PostgreSQL and come back as a 500.
INT32_MAX = 2**31 - 1

# Upper bound for a price per unit. Together with INT32_MAX it keeps
# quantity * price far from the limits of a double, and "Infinity" / "NaN"
# (which Python's JSON parser accepts) are refused: an infinite price stored in
# the database cannot be serialized back to JSON, which would break every
# request that lists offers.
MAX_PRICE = 1_000_000_000_000.0

# Free-text descriptions (faction, role) are stored as unbounded TEXT: cap them
# on input so nobody can fill the database with them.
MAX_DESCRIPTION_LENGTH = 5000


class PartialUpdate(BaseModel):
    """Base for PATCH/PUT-style bodies where every field is optional.

    "Field not sent" means "leave unchanged", which is fine. But an explicit
    `null` on a column that is NOT NULL used to reach the database and come
    back as a 500; it is rejected here with a 422 instead. Subclasses list the
    non-nullable fields in `non_nullable`.
    """

    non_nullable: ClassVar[tuple[str, ...]] = ()

    @model_validator(mode="after")
    def _reject_explicit_null(self):
        for name in self.non_nullable:
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"'{name}' cannot be null")
        return self
