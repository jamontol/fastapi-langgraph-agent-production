"""Shared Valkey (Redis) client and stream consumer-group helpers for the async task bus."""

import redis.asyncio as valkey

from app.core.config import settings

valkey_client = valkey.Redis(
    host=settings.VALKEY_HOST,
    port=settings.VALKEY_PORT,
    db=settings.VALKEY_DB,
    password=settings.VALKEY_PASSWORD or None,
    max_connections=settings.VALKEY_MAX_CONNECTIONS,
    decode_responses=True,
)

STREAM_KEY = "agent_tasks_stream"
CONSUMER_GROUP = "worker_group"


async def init_valkey_stream() -> None:
    """Ensure the task stream and its consumer group exist (idempotent)."""
    try:
        await valkey_client.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
    except valkey.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise
