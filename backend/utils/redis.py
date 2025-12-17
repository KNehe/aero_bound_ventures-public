from redis import asyncio as aioredis
import json
import asyncio

redis = aioredis.from_url("redis://redis:6379")


async def notification_streamer(user_id: str):
    pubsub = redis.pubsub()

    await pubsub.subscribe("notifications")

    while True:
        message = await pubsub.get_message(ignore_subscribe_messages=True)
        if message and message["type"] == "message":
            event = json.loads(message["data"])
            yield f"data: {json.dumps(event)}\n\n"
        await asyncio.sleep(0.01)
