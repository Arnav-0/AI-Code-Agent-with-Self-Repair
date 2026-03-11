"""Conversation API routes and WebSocket for the tool-using agent."""
from __future__ import annotations

import asyncio
import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict

from app.agents.tool_agent import ToolAgent
from app.config import get_settings

logger = logging.getLogger("codeforge.api.conversations")

router = APIRouter(prefix="/conversations", tags=["Conversations"])

# ── Pydantic schemas ────────────────────────────────────────────────────────


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    project_path: Optional[str] = None
    model: Optional[str] = None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: Optional[str] = None
    project_path: Optional[str] = None
    model_used: Optional[str] = None
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    status: str = "active"
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: Optional[str] = None
    tool_calls: Optional[list] = None
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None
    agent_role: Optional[str] = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    created_at: datetime


class ConversationDetail(ConversationResponse):
    messages: list[MessageResponse] = []


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class SendMessageRequest(BaseModel):
    content: str
    use_multi_agent: bool = False


class SendMessageResponse(BaseModel):
    message_id: uuid.UUID
    status: str = "processing"


# ── Running agent registry ──────────────────────────────────────────────────

_running_agents: dict[str, ToolAgent] = {}
_running_bg_tasks: dict[str, asyncio.Task] = {}

# WebSocket connections per conversation
_ws_connections: dict[str, list[WebSocket]] = {}


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


async def _broadcast(conversation_id: str, event_name: str, data: dict) -> None:
    """Broadcast a JSON event to all WebSocket connections for a conversation."""
    payload = {"event": event_name, "data": data, "timestamp": _now().isoformat()}
    dead: list[WebSocket] = []
    for ws in list(_ws_connections.get(conversation_id, [])):
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        try:
            _ws_connections.get(conversation_id, []).remove(ws)
        except ValueError:
            pass


# ── Dependency helpers ──────────────────────────────────────────────────────


async def _get_conversation_service():
    """Yield a ConversationService bound to a DB session."""
    from app.db.session import async_session_factory
    from app.services.conversation_service import ConversationService

    async with async_session_factory() as session:
        try:
            yield ConversationService(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── REST endpoints ──────────────────────────────────────────────────────────


@router.post("/", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    body: ConversationCreate,
    service=Depends(_get_conversation_service),
) -> ConversationResponse:
    """Create a new conversation."""
    settings = get_settings()
    model = body.model or getattr(settings, "agent_model", "openai/gpt-4o-mini")
    conv = await service.create_conversation(
        title=body.title,
        project_path=body.project_path,
        model=model,
    )
    return ConversationResponse.model_validate(conv)


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    service=Depends(_get_conversation_service),
) -> ConversationListResponse:
    """List conversations (paginated, newest first)."""
    conversations, total = await service.list_conversations(
        page=page, per_page=per_page
    )
    total_pages = max(1, math.ceil(total / per_page))
    return ConversationListResponse(
        items=[ConversationResponse.model_validate(c) for c in conversations],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: uuid.UUID,
    service=Depends(_get_conversation_service),
) -> ConversationDetail:
    """Get a conversation with its messages."""
    conv = await service.get_conversation(
        conversation_id, load_messages=True
    )
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationDetail.model_validate(conv)


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: uuid.UUID,
    service=Depends(_get_conversation_service),
) -> dict:
    """Delete a conversation and all its messages."""
    cid = str(conversation_id)

    # Cancel any running agent
    agent = _running_agents.pop(cid, None)
    if agent is not None:
        agent.cancel()
    bg = _running_bg_tasks.pop(cid, None)
    if bg is not None and not bg.done():
        bg.cancel()

    deleted = await service.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True}


@router.post(
    "/{conversation_id}/messages",
    response_model=SendMessageResponse,
    status_code=201,
)
async def send_message(
    conversation_id: uuid.UUID,
    body: SendMessageRequest,
    service=Depends(_get_conversation_service),
) -> SendMessageResponse:
    """Send a user message and trigger the agent in the background.

    The agent's events are streamed via the conversation WebSocket.
    """
    conv = await service.get_conversation(conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not body.content or not body.content.strip():
        raise HTTPException(status_code=422, detail="Message content cannot be empty")

    # Save user message
    user_msg = await service.add_message(
        conversation_id, role="user", content=body.content
    )

    cid = str(conversation_id)

    # Cancel previous agent if still running
    prev_agent = _running_agents.pop(cid, None)
    if prev_agent is not None:
        prev_agent.cancel()
    prev_bg = _running_bg_tasks.pop(cid, None)
    if prev_bg is not None and not prev_bg.done():
        prev_bg.cancel()

    # Launch agent in background
    bg_task = asyncio.create_task(
        _run_agent(
            conversation_id=conversation_id,
            use_multi_agent=body.use_multi_agent,
        )
    )
    _running_bg_tasks[cid] = bg_task
    bg_task.add_done_callback(lambda _: _cleanup_agent(cid))

    return SendMessageResponse(message_id=user_msg.id, status="processing")


@router.post("/{conversation_id}/stop")
async def stop_agent(conversation_id: uuid.UUID) -> dict:
    """Stop the running agent for a conversation."""
    cid = str(conversation_id)

    agent = _running_agents.get(cid)
    if agent is not None:
        agent.cancel()

    bg = _running_bg_tasks.get(cid)
    if bg is not None and not bg.done():
        bg.cancel()
        try:
            await asyncio.wait_for(asyncio.shield(bg), timeout=3.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

    _running_agents.pop(cid, None)
    _running_bg_tasks.pop(cid, None)

    await _broadcast(cid, "agent.stopped", {"message": "Agent stopped by user"})
    return {"success": True, "status": "stopped"}


# ── WebSocket endpoint ──────────────────────────────────────────────────────


@router.websocket("/ws/{conversation_id}")
async def conversation_websocket(
    websocket: WebSocket, conversation_id: str
) -> None:
    """Stream agent events for a conversation in real time."""
    await websocket.accept()

    if conversation_id not in _ws_connections:
        _ws_connections[conversation_id] = []
    _ws_connections[conversation_id].append(websocket)
    logger.info("WS connected for conversation %s", conversation_id)

    try:
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(), timeout=15
                )
            except asyncio.TimeoutError:
                # Keepalive ping
                try:
                    await websocket.send_json(
                        {"event": "ping", "timestamp": _now().isoformat()}
                    )
                except Exception:
                    break
                continue

            # Handle client-side stop request
            if data.get("event") == "agent.stop":
                agent = _running_agents.get(conversation_id)
                if agent is not None:
                    agent.cancel()
                bg = _running_bg_tasks.get(conversation_id)
                if bg is not None and not bg.done():
                    bg.cancel()
                await websocket.send_json(
                    {
                        "event": "agent.stopped",
                        "data": {"message": "Agent stop requested"},
                        "timestamp": _now().isoformat(),
                    }
                )

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error(
            "WebSocket error for conversation %s: %s",
            conversation_id,
            exc,
        )
    finally:
        try:
            _ws_connections.get(conversation_id, []).remove(websocket)
        except ValueError:
            pass
        if not _ws_connections.get(conversation_id):
            _ws_connections.pop(conversation_id, None)
        logger.info("WS disconnected for conversation %s", conversation_id)


# ── Background agent runner ────────────────────────────────────────────────


def _cleanup_agent(conversation_id: str) -> None:
    _running_agents.pop(conversation_id, None)
    _running_bg_tasks.pop(conversation_id, None)


async def _run_agent(
    *,
    conversation_id: uuid.UUID,
    use_multi_agent: bool = False,
) -> None:
    """Background task: run the tool agent and persist results."""
    cid = str(conversation_id)

    try:
        from app.agents.prompts.tool_agent import ROLE_PROMPTS
        from app.db.session import async_session_factory
        from app.services.conversation_service import ConversationService
        from app.tools.registry import create_tool_registry

        settings = get_settings()
        api_key = settings.openrouter_api_key
        if not api_key:
            await _broadcast(
                cid, "agent.error", {"error": "OpenRouter API key not configured"}
            )
            return

        model = getattr(settings, "agent_model", "openai/gpt-4o-mini")
        max_iterations = getattr(settings, "agent_max_iterations", 25)
        workspace_root = getattr(
            settings, "agent_workspace_root", "/tmp/codeforge-workspace"
        )

        # Get conversation and project path
        async with async_session_factory() as session:
            svc = ConversationService(session)
            conv = await svc.get_conversation(conversation_id)
            if conv is None:
                await _broadcast(
                    cid, "agent.error", {"error": "Conversation not found"}
                )
                return

            # Use project_path if set, otherwise workspace_root
            ws_root = conv.project_path or workspace_root

            # Build message history for LLM
            messages = await svc.get_messages_for_llm(conversation_id)

        # Create tool registry scoped to workspace
        tools = create_tool_registry(ws_root)

        # Create agent
        if use_multi_agent:
            from app.agents.multi_agent import MultiAgent

            agent_obj = MultiAgent(
                api_key=api_key,
                model=model,
                base_tools=tools,
                max_iterations=max_iterations,
                specialist_max_iterations=max(10, max_iterations // 2),
            )
            _running_agents[cid] = agent_obj  # type: ignore[assignment]

            event_gen = agent_obj.run(messages)
        else:
            agent_obj = ToolAgent(
                api_key=api_key,
                model=model,
                tools=tools,
                system_prompt=ROLE_PROMPTS["main"],
                role="main",
                max_iterations=max_iterations,
            )
            _running_agents[cid] = agent_obj

            event_gen = agent_obj.run(messages)

        # Collect assistant response data for DB persistence
        final_text: Optional[str] = None
        all_tool_calls: list[dict] = []
        total_tokens = 0

        # Process events
        async for event in event_gen:
            # Map event types to WebSocket event names
            event_map = {
                "thinking": "agent.thinking",
                "tool_call": "tool.call",
                "tool_result": "tool.result",
                "text": "agent.text",
                "error": "agent.error",
                "done": "agent.done",
                "agent_switch": "agent.switch",
            }
            ws_event_name = event_map.get(event.type, f"agent.{event.type}")
            await _broadcast(cid, ws_event_name, event.data)

            # Collect data for persistence
            if event.type == "text":
                final_text = event.data.get("content", "")
            elif event.type == "tool_call":
                all_tool_calls.append(
                    {
                        "id": event.data.get("id", ""),
                        "type": "function",
                        "function": {
                            "name": event.data.get("name", ""),
                            "arguments": event.data.get("arguments", {}),
                        },
                    }
                )
            elif event.type == "done":
                total_tokens = event.data.get("total_tokens", 0)

        # Persist assistant message(s) to DB
        async with async_session_factory() as session:
            svc = ConversationService(session)

            # Save tool calls as individual messages if any
            for tc in all_tool_calls:
                await svc.add_message(
                    conversation_id,
                    role="assistant",
                    content=None,
                    tool_calls=[tc],
                    agent_role="main",
                )

            # Save final assistant text
            if final_text:
                await svc.add_message(
                    conversation_id,
                    role="assistant",
                    content=final_text,
                    agent_role="main",
                    tokens_used=total_tokens,
                )

            # Update conversation totals
            await svc.update_conversation(
                conversation_id,
                total_tokens=(conv.total_tokens or 0) + total_tokens,
            )

            await session.commit()

    except asyncio.CancelledError:
        logger.info("Agent for conversation %s was cancelled", cid)
        await _broadcast(
            cid, "agent.stopped", {"message": "Agent was cancelled"}
        )

    except Exception as exc:
        logger.error(
            "Agent failed for conversation %s: %s", cid, exc, exc_info=True
        )
        await _broadcast(
            cid, "agent.error", {"error": f"Agent failed: {exc}"}
        )
