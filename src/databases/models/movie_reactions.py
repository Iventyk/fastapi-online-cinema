from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.databases.models.base import Base


class MovieReaction(Base):
    __tablename__ = "movie_reactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"),
        nullable=False,
    )

    value: Mapped[int] = mapped_column(Integer, nullable=False)

    user = relationship("UserModel")
    movie = relationship("Movie", back_populates="reactions")

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "movie_id",
            name="uq_user_movie_reaction",
        ),
    )
