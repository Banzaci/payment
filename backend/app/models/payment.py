
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    merchant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("merchants.id"),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    network: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    recipient_address: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )

    reference: Mapped[str] = mapped_column(
        String(44),
        unique=True,
        nullable=False,
    )

    payment_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
