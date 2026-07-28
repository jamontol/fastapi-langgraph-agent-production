import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.api.v1.auth import get_current_session
from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import logger
from app.services.stream import valkey_client, enqueue_agent_task
from app.models.session import Session
from app.schemas.chat import ChatRequest, ChatResponse, StreamResponse
from app.services.session_naming import maybe_name_session

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["chat"][0])
async def chat(
    request: Request,
    chat_request: ChatRequest,
    session: Session = Depends(get_current_session),
):
    try:
        logger.info(
            "chat_request_received",
            session_id=session.id,
            message_count=len(chat_request.messages),
        )

        if settings.SESSION_NAMING_ENABLED:
            maybe_name_session(session.id, session.name, chat_request.messages)

        # 1. Prepare payload for the stream
        payload = {
            "session_id": session.id,
            "user_id": str(session.user_id),
            "username": session.username,
            "messages": [m.model_dump(mode="json") for m in chat_request.messages],
            "stream": False,
        }

        # 2. Enqueue task in Valkey Stream
        task_id = await enqueue_agent_task(payload)
        
        # 3. Wait for final result via Pub/Sub channel
        pubsub = valkey_client.pubsub()
        channel_name = f"task_result:{task_id}"
        await pubsub.subscribe(channel_name)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    if "error" in data:
                        raise HTTPException(status_code=500, detail=data["error"])
                    return ChatResponse(messages=data["messages"])
        finally:
            await pubsub.unsubscribe(channel_name)

    except Exception as e:
        logger.exception("chat_request_failed", session_id=session.id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["chat_stream"][0])
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    session: Session = Depends(get_current_session),
):
    try:
        logger.info(
            "stream_chat_request_received",
            session_id=session.id,
            message_count=len(chat_request.messages),
        )

        if settings.SESSION_NAMING_ENABLED:
            maybe_name_session(session.id, session.name, chat_request.messages)

        # 1. Prepare task payload
        payload = {
            "session_id": session.id,
            "user_id": str(session.user_id),
            "username": session.username,
            "messages": [m.model_dump(mode="json") for m in chat_request.messages],
            "stream": True,
        }

        # 2. Enqueue to Valkey Stream
        task_id = await enqueue_agent_task(payload)

        async def event_generator():
            pubsub = valkey_client.pubsub()
            channel_name = f"task_stream:{task_id}"
            await pubsub.subscribe(channel_name)

            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        data = json.loads(message["data"])
                        
                        # Handle errors
                        if "error" in data:
                            err_resp = StreamResponse(content=data["error"], done=True)
                            yield f"data: {json.dumps(err_resp.model_dump(mode='json'))}\n\n"
                            break

                        # Check for completion flag
                        if data.get("done", False):
                            final_response = StreamResponse(content="", done=True)
                            yield f"data: {json.dumps(final_response.model_dump(mode='json'))}\n\n"
                            break

                        # Stream content chunk
                        response = StreamResponse(content=data.get("content", ""), done=False)
                        yield f"data: {json.dumps(response.model_dump(mode='json'))}\n\n"
            finally:
                await pubsub.unsubscribe(channel_name)

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        logger.exception(
            "stream_chat_request_failed",
            session_id=session.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))