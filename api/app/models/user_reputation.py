from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserReputation(Base):
    __tablename__ = "user_reputation"

    id: Mapped[int] = mapped_column(primary_key=True)

    from_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    to_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "from_user_id",
            "to_user_id",
            name="uq_user_reputation_pair",
        ),
        CheckConstraint(
            "from_user_id != to_user_id",
            name="ck_user_reputation_no_self",
        ),
    )

    from_user = relationship(
        "User",
        foreign_keys=[from_user_id],
        backref="reputation_given",
    )

    to_user = relationship(
        "User",
        foreign_keys=[to_user_id],
        backref="reputation_received",
    )
