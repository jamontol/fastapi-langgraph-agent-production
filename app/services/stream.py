import json
import uuid
import asyncio
import redis.asyncio as valkey
from app.core.config import settings

# Initialize Valkey client (adjust environment variables as needed)
valkey_client = valkey.Redis(
    host=getattr(settings, "VALKEY_HOST", "valkey"),
    port=getattr(settings, "VALKEY_PORT", 6379),
    decode_responses=True,
)

STREAM_KEY = "agent_tasks_stream"
CONSUMER_GROUP = "worker_group"

async def init_valkey_stream():
    """Ensure stream consumer group exists."""
    try:
        await valkey_client.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
    except valkey.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise e

async def enqueue_agent_task(payload: dict) -> str:
    """Push a task to the Valkey Stream and return the task_id."""
    task_id = str(uuid.uuid4())
    payload["task_id"] = task_id
    
    # Send serialized JSON to Valkey Stream
    await valkey_client.xadd(STREAM_KEY, {"payload": json.dumps(payload)})
    return task_id