"""Pure boundary conversions, shared by repositories and serializers."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID


def utc_now() -> datetime:
    return datetime.now(UTC)


def to_db_time(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("A timezone-aware timestamp is required")
    result = value.astimezone(UTC).replace(tzinfo=None)
    if result.year < 1000:
        raise ValueError("Timestamp is outside the frozen database domain")
    return result


def from_db_time(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def hours_to_quarters(value) -> int:
    if isinstance(value, bool):
        raise ValueError("Hours must be a number")
    quarters = Decimal(str(value)) * 4
    if not quarters.is_finite() or quarters < 0 or quarters != quarters.to_integral_value():
        raise ValueError("Hours must be a nonnegative multiple of 0.25")
    return int(quarters)


def quarters_to_hours(value: int) -> Decimal:
    return Decimal(value) / 4


def uuid_to_bytes(value: str | UUID) -> bytes:
    return UUID(str(value)).bytes


def bytes_to_uuid(value: bytes) -> str:
    return str(UUID(bytes=value))
