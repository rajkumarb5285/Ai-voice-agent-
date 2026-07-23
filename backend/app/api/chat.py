"""
Chat API — REST + WebSocket streaming
WebSocket endpoint delivers real-time agent activity updates and streaming text.
"""
import uuid
import json
import time
import asyncio
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.conversation import Conversation, Message, MessageRole
from app.models.schemas import ChatRequest, ConversationResponse
from app.agents.graph import run_agent
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Non-streaming chat endpoint — returns full response."""
    conversation_id = request.conversation_id or str(uuid.uuid4())
    user_id = str(current_user.id)

    # Ensure conversation exists
    await _get_or_create_conversation(db, conversation_id, user_id, request.mode)

    start = time.time()
    result = await run_agent(
        user_input=request.message,
        user_id=user_id,
        conversation_id=conversation_id,
        input_mode=request.mode,
        db=db,
    )

    final_response = result.get("final_response", "I couldn't process that request.")

    # Save messages
    await _save_message(db, conversation_id, "user", request.message, intent=result.get("intent"))
    await _save_message(
        db, conversation_id, "assistant", final_response,
        agent_name=result.get("intent"),
        tool_calls=result.get("agent_activities"),
        latency_ms=int((time.time() - start) * 1000),
    )

    return {
        "conversation_id": conversation_id,
        "response": final_response,
        "intent": result.get("intent"),
        "agents_used": result.get("selected_agents", []),
        "agent_activities": result.get("agent_activities", []),
        "plan": result.get("plan"),
        "latency_ms": result.get("total_latency_ms"),
    }


@router.websocket("/ws/{conversation_id}")
async def chat_websocket(
    websocket: WebSocket,
    conversation_id: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket streaming endpoint.
    Client sends: {"message": "...", "mode": "chat|voice"}
    Server streams: agent_activity events, then text chunks, then done
    """
    await websocket.accept()

    # Validate token
    from app.services.auth_service import decode_token, get_user_by_id
    token_data = decode_token(token)
    if not token_data:
        logger.warning("websocket_invalid_token", conversation_id=conversation_id)
        await websocket.send_json({"type": "error", "code": "auth_error", "content": "Invalid or expired token — please log in again"})
        await websocket.close(code=4001)
        return

    user = await get_user_by_id(db, token_data.user_id)
    if not user:
        logger.warning("websocket_user_not_found", user_id=token_data.user_id, conversation_id=conversation_id)
        await websocket.send_json({"type": "error", "code": "auth_error", "content": "Session expired — please log in again"})
        await websocket.close(code=4001)
        return

    user_id = str(user.id)
    logger.info("websocket_connected", user_id=user_id, conversation_id=conversation_id)

    # Send connected confirmation ping
    await websocket.send_json({"type": "connected", "user_id": user_id})

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            message = data.get("message", "")
            mode = data.get("mode", "chat")
            language = data.get("language", "en-US")

            if not message.strip():
                continue

            await websocket.send_json({
                "type": "status",
                "content": "Processing...",
            })

            # Ensure the conversation record exists in DB before saving messages
            await _get_or_create_conversation(db, conversation_id, user_id, mode)

            # Run agent pipeline
            try:
                tag_buffer = ""
                in_tag = False

                async def on_token(token: str):
                    nonlocal in_tag, tag_buffer
                    try:
                        for char in token:
                            if char == '[':
                                in_tag = True
                                tag_buffer = "["
                            elif in_tag:
                                tag_buffer += char
                                if char == ']':
                                    in_tag = False
                                    if tag_buffer.startswith("[action:") or tag_buffer.startswith("[emotion:"):
                                        tag_buffer = ""
                                    else:
                                        await websocket.send_json({
                                            "type": "text",
                                            "content": tag_buffer,
                                        })
                                        tag_buffer = ""
                            else:
                                await websocket.send_json({
                                    "type": "text",
                                    "content": char,
                                })
                    except Exception:
                        pass

                result = await run_agent(
                    user_input=message,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    input_mode=mode,
                    language=language,
                    db=db,
                    on_token_callback=on_token,
                )

                # Stream agent activities first
                for activity in result.get("agent_activities", []):
                    await websocket.send_json({
                        "type": "agent_activity",
                        "agent_activity": activity,
                    })
                    await asyncio.sleep(0.01)

                final_response = result.get("final_response", "")

                # Parse actions and emotions
                import re
                actions = re.findall(r'\[action:\s*(\w+)\]', final_response)
                emotions = re.findall(r'\[emotion:\s*(\w+)\]', final_response)

                # Clean response for saving to database
                cleaned_response = re.sub(r'\[action:\s*\w+\]', '', final_response)
                cleaned_response = re.sub(r'\[emotion:\s*\w+\]', '', cleaned_response).strip()

                # Done signal
                await websocket.send_json({
                    "type": "done",
                    "metadata": {
                        "intent": result.get("intent"),
                        "agents_used": result.get("selected_agents", []),
                        "latency_ms": result.get("total_latency_ms"),
                        "plan": result.get("plan"),
                        "actions": actions,
                        "emotions": emotions,
                    },
                })

                # Save to DB
                await _save_message(db, conversation_id, "user", message)
                await _save_message(db, conversation_id, "assistant", cleaned_response)

                # Auto-title the conversation on first message
                await _auto_title_conversation(db, conversation_id, message)

            except Exception as e:
                logger.error("websocket_agent_error", error=str(e))
                await websocket.send_json({
                    "type": "error",
                    "content": f"Agent error: {str(e)}",
                })

    except WebSocketDisconnect:
        logger.info("websocket_disconnected", user_id=user_id)


@router.get("/conversations", response_model=List[dict])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
):
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == current_user.id, Conversation.is_active == True)
        .order_by(desc(Conversation.updated_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    convos = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "title": c.title or "New conversation",
            "mode": c.mode,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }
        for c in convos
    ]


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    import uuid
    if isinstance(conversation_id, str):
        try:
            conversation_id = uuid.UUID(conversation_id)
        except ValueError:
            pass
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .limit(limit)
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "role": m.role.value,
            "content": m.content,
            "agent_name": m.agent_name,
            "intent": m.intent,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def _get_or_create_conversation(
    db: AsyncSession,
    conversation_id: str,
    user_id: str,
    mode: str = "chat",
) -> Conversation:
    import uuid
    if isinstance(conversation_id, str):
        try:
            conversation_id = uuid.UUID(conversation_id)
        except ValueError:
            pass
    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except ValueError:
            pass
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(stmt)
    convo = result.scalar_one_or_none()
    if not convo:
        convo = Conversation(
            id=conversation_id,
            user_id=user_id,
            mode=mode,
            title=None,
        )
        db.add(convo)
        await db.commit()
    return convo


async def _save_message(
    db: AsyncSession,
    conversation_id: str,
    role: str,
    content: str,
    agent_name: Optional[str] = None,
    intent: Optional[str] = None,
    tool_calls: Optional[list] = None,
    latency_ms: Optional[int] = None,
) -> Message:
    import uuid
    if isinstance(conversation_id, str):
        try:
            conversation_id = uuid.UUID(conversation_id)
        except ValueError:
            pass
    msg = Message(
        conversation_id=conversation_id,
        role=MessageRole(role),
        content=content,
        agent_name=agent_name,
        intent=intent,
        tool_calls=tool_calls or [],
        latency_ms=latency_ms,
    )
    db.add(msg)
    await db.commit()
    return msg
async def _auto_title_conversation(
    db: AsyncSession,
    conversation_id: str,
    first_message: str,
) -> None:
    """Set conversation title to first message if not already set."""
    import uuid
    conv_id = uuid.UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
    stmt = select(Conversation).where(Conversation.id == conv_id)
    result = await db.execute(stmt)
    convo = result.scalar_one_or_none()
    if convo and not convo.title:
        # Truncate to 60 chars, strip newlines
        title = first_message.strip().replace("\n", " ")[:60]
        if len(first_message.strip()) > 60:
            title += "…"
        convo.title = title
        await db.commit()
