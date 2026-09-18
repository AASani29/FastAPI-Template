"""SQLAlchemy models — two tables, no inheritance, no mixins.

Note there are no `relationship()` attributes. Nothing in this app navigates
from a user to its items in Python; every service issues an explicit query
filtered by owner_id. Under async SQLAlchemy an unloaded relationship raises
MissingGreenlet the moment something touches it, so declaring relationships we
never load would add a footgun and no capability.

`Item` is a template resource: a generic, owner-scoped, timestamped row meant
to be copied when you add your own domain model, not used as-is. Duplicate
this class, its schema, its service, and its route file for each new resource.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 320 = the maximum length of an email address per RFC 5321.
    # Unique because it is the login identifier; enforced by the database so a
    # race between two concurrent registrations cannot create a duplicate.
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    # The bcrypt hash, never the password. Always 60 chars for bcrypt, but sized
    # larger so swapping the algorithm later does not need a migration.
    hashed_password: Mapped[str] = mapped_column(String(128))
    # server_default so the database stamps the time. A Python-side default
    # would use the app server's clock, which drifts from the DB's.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # ondelete CASCADE: deleting a user must not leave orphan rows pointing at
    # a vanished id. Enforced in the database, so it holds for the seed script
    # and manual psql sessions too, not just for traffic through the ORM.
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
