import asyncio
import json
from app.core.langgraph.graph import LangGraphAgent
from app.core.logging import logger
from app.core.valkey import valkey_client, STREAM_KEY, CONSUMER_GROUP, init_valkey_stream

agent = LangGraphAgent()
WORKER_NAME = "worker-1"

async def process_stream_task(task_id: str, payload: dict):
    """Executes streaming LangGraph workflow and publishes chunks."""
    channel_name = f"task_stream:{task_id}"
    try:
        messages = payload["messages"]
        session_id = payload["session_id"]
        user_id = payload["user_id"]
        username = payload["username"]

        async for chunk in agent.get_stream_response(
            messages, session_id, user_id=user_id, username=username
        ):
            await valkey_client.publish(
                channel_name, json.dumps({"content": chunk, "done": False})
            )

        # Signal stream completion
        await valkey_client.publish(channel_name, json.dumps({"done": True}))

    except Exception as e:
        logger.exception("worker_stream_task_failed", task_id=task_id, error=str(e))
        await valkey_client.publish(
            channel_name, json.dumps({"error": str(e), "done": True})
        )

async def process_sync_task(task_id: str, payload: dict):
    """Executes standard LangGraph workflow and publishes final result."""
    channel_name = f"task_result:{task_id}"
    try:
        messages = payload["messages"]
        session_id = payload["session_id"]
        user_id = payload["user_id"]
        username = payload["username"]

        result = await agent.get_response(
            messages, session_id, user_id=user_id, username=username
        )
        await valkey_client.publish(
            channel_name, json.dumps({"messages": result})
        )
    except Exception as e:
        logger.exception("worker_sync_task_failed", task_id=task_id, error=str(e))
        await valkey_client.publish(channel_name, json.dumps({"error": str(e)}))

async def start_worker():
    await init_valkey_stream()
    logger.info("worker_started", worker=WORKER_NAME)

    while True:
        try:
            # Read new tasks from the Valkey Stream
            entries = await valkey_client.xreadgroup(
                CONSUMER_GROUP, WORKER_NAME, {STREAM_KEY: ">"}, count=1, block=2000
            )

            if not entries:
                continue

            for stream_name, messages in entries:
                for message_id, message_data in messages:
                    payload = json.loads(message_data["payload"])
                    task_id = payload["task_id"]

                    if payload.get("stream", False):
                        await process_stream_task(task_id, payload)
                    else:
                        await process_sync_task(task_id, payload)

                    # Acknowledge task processing complete
                    await valkey_client.xack(STREAM_KEY, CONSUMER_GROUP, message_id)

        except Exception as e:
            logger.exception("worker_loop_error", error=str(e))
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(start_worker())