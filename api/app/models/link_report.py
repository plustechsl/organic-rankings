from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

from app.database import Base


class LinkReport(Base):
    __tablename__ = "link_reports"

    id: Mapped[int] = mapped_column(primary_key=True)

    link_id: Mapped[int] = mapped_column(
        ForeignKey("links.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reason: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "link_id",
            "user_id",
            name="uq_link_reports_link_user",
        ),
    )

    link = relationship(
        "Link",
        backref=backref(
            "reports",
            cascade="all, delete-orphan",
            passive_deletes=True,
        ),
    )

    user = relationship(
        "User",
        backref="link_reports",
    )
