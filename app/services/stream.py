"""Task enqueue helper for the Valkey Stream-based async worker bus."""

import json
import uuid

from app.core.valkey import STREAM_KEY, valkey_client


async def enqueue_agent_task(payload: dict) -> str:
    """Push a task to the Valkey Stream and return the task_id."""
    task_id = str(uuid.uuid4())
    payload["task_id"] = task_id

    await valkey_client.xadd(STREAM_KEY, {"payload": json.dumps(payload)})
    return task_id
