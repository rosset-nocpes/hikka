from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timedelta, UTC
from ..mixins import NeedsSearchUpdateMixin
from sqlalchemy.orm import query_expression
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from sqlalchemy import ForeignKey
from sqlalchemy import String
from ..base import Base


class User(Base, NeedsSearchUpdateMixin):
    __tablename__ = "service_users"

    email: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    role: Mapped[str] = mapped_column(String(64), index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(60), nullable=True)
    description: Mapped[str] = mapped_column(String(140), nullable=True)
    username: Mapped[str] = mapped_column(String(64), index=True)
    email_confirmed: Mapped[bool] = mapped_column(default=False)
    banned: Mapped[bool] = mapped_column(default=False)

    activation_token: Mapped[str] = mapped_column(String(64), nullable=True)
    activation_expire: Mapped[datetime] = mapped_column(nullable=True)

    password_reset_token: Mapped[str] = mapped_column(String(64), nullable=True)
    password_reset_expire: Mapped[datetime] = mapped_column(nullable=True)

    last_username_change: Mapped[datetime] = mapped_column(nullable=True)
    last_email_change: Mapped[datetime] = mapped_column(nullable=True)

    ignored_notifications: Mapped[list] = mapped_column(JSONB, default=[])
    updated: Mapped[datetime] = mapped_column(nullable=True)
    last_active: Mapped[datetime]
    created: Mapped[datetime]
    login: Mapped[datetime]

    is_followed: Mapped[bool] = query_expression()

    email_messages: Mapped[list["EmailMessage"]] = relationship(
        back_populates="user",
    )

    auth_tokens: Mapped[list["AuthToken"]] = relationship(
        back_populates="user",
    )

    followers: Mapped[list["Follow"]] = relationship(
        foreign_keys="[Follow.followed_user_id]",
        back_populates="followed_user",
    )

    following: Mapped[list["Follow"]] = relationship(
        foreign_keys="[Follow.user_id]", back_populates="user"
    )

    watch: Mapped[list["AnimeWatch"]] = relationship(
        foreign_keys="[AnimeWatch.user_id]", back_populates="user"
    )

    oauth_providers: Mapped[list["UserOAuth"]] = relationship(
        foreign_keys="[UserOAuth.user_id]", back_populates="user"
    )

    edits: Mapped[list["Edit"]] = relationship(
        foreign_keys="[Edit.author_id]", back_populates="author"
    )

    comments: Mapped[list["Comment"]] = relationship(
        foreign_keys="[Comment.author_id]", back_populates="author"
    )

    decisions: Mapped[list["Edit"]] = relationship(
        foreign_keys="[Edit.moderator_id]", back_populates="moderator"
    )
    avatar_image_id = mapped_column(
        ForeignKey("service_images.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    cover_image_id = mapped_column(
        ForeignKey("service_images.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    avatar_image_relation: Mapped["Image"] = relationship(
        foreign_keys=[avatar_image_id], lazy="selectin"
    )

    cover_image_relation: Mapped["Image"] = relationship(
        foreign_keys=[cover_image_id], lazy="selectin"
    )

    @hybrid_property
    def avatar(self):
        if not self.avatar_image_relation:
            return "https://cdn.hikka.io/avatar.jpg"

        if (
            self.avatar_image_relation.ignore
            or not self.avatar_image_relation.uploaded
        ):
            return "https://cdn.hikka.io/avatar.jpg"

        return self.avatar_image_relation.url

    @hybrid_property
    def cover(self):
        if not self.cover_image_relation:
            return None

        if (
            self.cover_image_relation.ignore
            or not self.cover_image_relation.uploaded
        ):
            return None

        return self.cover_image_relation.url

    @hybrid_property
    def active(self):
        now = datetime.now(UTC).replace(tzinfo=None)
        return self.last_active + timedelta(minutes=10) > now
