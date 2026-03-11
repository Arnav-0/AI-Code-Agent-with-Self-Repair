"""Service layer for conversation CRUD and message management."""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, Message


class ConversationService:
    """Async service for managing conversations and their messages."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Conversation CRUD ───────────────────────────────────────────────

    async def create_conversation(
        self,
        *,
        title: Optional[str] = None,
        project_path: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Conversation:
        conv = Conversation(
            title=title or "New conversation",
            project_path=project_path,
            model_used=model,
            status="active",
        )
        self.session.add(conv)
        await self.session.flush()
        await self.session.refresh(conv)
        return conv

    async def get_conversation(
        self, conversation_id: uuid.UUID, *, load_messages: bool = False
    ) -> Optional[Conversation]:
        stmt = select(Conversation).where(
            Conversation.id == conversation_id
        )
        if load_messages:
            stmt = stmt.options(selectinload(Conversation.messages))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_conversations(
        self, *, page: int = 1, per_page: int = 20
    ) -> tuple[list[Conversation], int]:
        # Count
        count_stmt = select(func.count()).select_from(Conversation)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        # Fetch page
        offset = (page - 1) * per_page
        stmt = (
            select(Conversation)
            .order_by(desc(Conversation.updated_at))
            .offset(offset)
            .limit(per_page)
        )
        result = await self.session.execute(stmt)
        conversations = list(result.scalars().all())

        return conversations, total

    async def delete_conversation(
        self, conversation_id: uuid.UUID
    ) -> bool:
        conv = await self.session.get(Conversation, conversation_id)
        if conv is None:
            return False
        await self.session.delete(conv)
        await self.session.flush()
        return True

    async def update_conversation(
        self,
        conversation_id: uuid.UUID,
        *,
        title: Optional[str] = None,
        status: Optional[str] = None,
        total_tokens: Optional[int] = None,
        total_cost_usd: Optional[Decimal] = None,
    ) -> Optional[Conversation]:
        conv = await self.session.get(Conversation, conversation_id)
        if conv is None:
            return None
        if title is not None:
            conv.title = title
        if status is not None:
            conv.status = status
        if total_tokens is not None:
            conv.total_tokens = total_tokens
        if total_cost_usd is not None:
            conv.total_cost_usd = total_cost_usd
        await self.session.flush()
        await self.session.refresh(conv)
        return conv

    # ── Messages ────────────────────────────────────────────────────────

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        *,
        role: str,
        content: Optional[str] = None,
        tool_calls: Optional[list] = None,
        tool_call_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        agent_role: Optional[str] = None,
        tokens_used: int = 0,
        cost_usd: Decimal = Decimal("0"),
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            agent_role=agent_role,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
        )
        self.session.add(msg)
        await self.session.flush()
        await self.session.refresh(msg)
        return msg

    async def get_messages(
        self,
        conversation_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_messages_for_llm(
        self, conversation_id: uuid.UUID, *, limit: int = 50
    ) -> list[dict]:
        """Build a message list suitable for the LLM API.

        Returns the most recent ``limit`` messages in chronological order,
        formatted as {"role": ..., "content": ..., ...} dicts.
        """
        msgs = await self.get_messages(
            conversation_id, limit=limit
        )

        llm_messages: list[dict] = []
        for m in msgs:
            entry: dict = {"role": m.role}

            if m.content is not None:
                entry["content"] = m.content

            if m.tool_calls:
                entry["tool_calls"] = m.tool_calls

            if m.tool_call_id:
                entry["tool_call_id"] = m.tool_call_id

            # Ensure tool messages always have content
            if m.role == "tool" and "content" not in entry:
                entry["content"] = ""

            llm_messages.append(entry)

        return llm_messages
