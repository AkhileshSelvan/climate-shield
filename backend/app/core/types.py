"""Exact-decimal money column.

Currency must never round-trip through a float. PostgreSQL stores NUMERIC(14,2)
natively; SQLite has no decimal type and SQLAlchemy would otherwise convert via
float, so on SQLite the value is persisted as a zero-padded string that both
sorts and compares correctly. Both dialects return `decimal.Decimal`.
"""
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.types import TypeDecorator

MONEY_PRECISION = 14
MONEY_SCALE = 2
TWO_PLACES = Decimal("0.01")


def quantize_money(value) -> Decimal:
    """Coerce to Decimal with exactly two places, rounding half-up."""
    if not isinstance(value, Decimal):
        # str() first: Decimal(float) would inherit the float's binary error.
        value = Decimal(str(value))
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


class Money(TypeDecorator):
    """NUMERIC(14,2) on PostgreSQL, lexicographically sortable text on SQLite."""

    impl = Numeric(MONEY_PRECISION, MONEY_SCALE, asdecimal=True)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(32))
        return dialect.type_descriptor(
            Numeric(MONEY_PRECISION, MONEY_SCALE, asdecimal=True)
        )

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        value = quantize_money(value)
        if dialect.name == "sqlite":
            # Zero-pad so string ordering matches numeric ordering.
            return f"{value:018.2f}"
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return quantize_money(value)
