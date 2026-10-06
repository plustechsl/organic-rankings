from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LinkTag(Base):
    __tablename__ = "link_tags"

    link_id: Mapped[int] = mapped_column(
        ForeignKey("links.id", ondelete="CASCADE"),
        nullable=False,
    )

    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        PrimaryKeyConstraint("link_id", "tag_id"),
    )

    link = relationship(
        "Link",
        back_populates="tag_relations",
    )

    tag = relationship(
        "Tag",
        back_populates="link_relations",
    )
