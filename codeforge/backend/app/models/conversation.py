"""SQLAlchemy models for the conversational agent pipeline."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Conversation(Base):
    """A multi-turn conversation with the tool-using agent."""

    __tablename__ = "conversations"

    title: Mapped[Optional[str]] = mapped_column(String(200))
    project_path: Mapped[Optional[str]] = mapped_column(String(500))
    model_used: Mapped[Optional[str]] = mapped_column(String(100))
    total_tokens: Mapped[int] = mapped_column(default=0)
    total_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), default=0
    )
    status: Mapped[str] = mapped_column(String(20), default="active")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    """A single message within a conversation (user, assistant, or tool)."""

    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # user, assistant, tool
    content: Mapped[Optional[str]] = mapped_column(Text)
    tool_calls: Mapped[Optional[list]] = mapped_column(JSON)
    tool_call_id: Mapped[Optional[str]] = mapped_column(String(100))
    tool_name: Mapped[Optional[str]] = mapped_column(String(100))
    agent_role: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # which agent role produced this message
    tokens_used: Mapped[int] = mapped_column(default=0)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=0)

    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )
