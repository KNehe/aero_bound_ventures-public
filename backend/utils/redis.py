"""Redis utilities for SSE notifications with pub/sub"""

from redis import asyncio as aioredis
import json
import asyncio
import uuid
import os
import logging

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

redis = aioredis.from_url(REDIS_URL, decode_responses=True)

# Heartbeat interval in seconds
HEARTBEAT_INTERVAL = 30


async def notification_streamer(user_id: uuid.UUID, initial_count: int = 0):
    """
    SSE stream generator for real-time notifications.

    Subscribes to a user-specific Redis channel and yields notifications
    as SSE events. Includes heartbeat to keep connection alive.

    Args:
        user_id: The UUID of the user to stream notifications for
        initial_count: The initial unread count to send on connection

    Yields:
        SSE formatted strings with notification data or keepalive comments
    """
    pubsub = redis.pubsub()
    channel = f"notifications:{user_id}"

    try:
        await pubsub.subscribe(channel)
        logger.info(f"SSE notification stream established for user {user_id}")

        # Send initial connection event with unread count
        yield f"event: connected\ndata: {json.dumps({'status': 'connected', 'user_id': str(user_id), 'unread_count': initial_count})}\n\n"

        while True:
            try:
                # Wait for message with timeout for heartbeat
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True),
                    timeout=HEARTBEAT_INTERVAL,
                )

                if message and message["type"] == "message":
                    event_data = json.loads(message["data"])
                    event_type = event_data.get("event_type", "notification")
                    yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"

            except asyncio.TimeoutError:
                # Send heartbeat comment to keep connection alive
                yield ": heartbeat\n\n"

    except asyncio.CancelledError:
        logger.info(f"SSE notification stream cancelled for user {user_id}")
        raise
    except Exception as e:
        logger.error(f"SSE notification stream error for user {user_id}: {e}")
        yield f"event: error\ndata: {json.dumps({'error': 'stream_error'})}\n\n"
    finally:
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
        except Exception as e:
            logger.warning(f"Error closing notification pubsub for user {user_id}: {e}")


async def unread_count_streamer(user_id: uuid.UUID, initial_count: int = 0):
    """
    SSE stream generator specifically for unread count updates.

    This is a lightweight stream that only sends unread count updates,
    ideal for displaying notification badges that need instant updates.

    Args:
        user_id: The UUID of the user to stream count for
        initial_count: The initial unread count from database

    Yields:
        SSE formatted strings with count data or keepalive comments
    """
    pubsub = redis.pubsub()
    channel = f"notifications:count:{user_id}"

    try:
        await pubsub.subscribe(channel)
        logger.info(f"SSE unread count stream established for user {user_id}")

        # Send initial count immediately
        yield f"event: count\ndata: {json.dumps({'unread_count': initial_count})}\n\n"

        while True:
            try:
                # Wait for message with timeout for heartbeat
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True),
                    timeout=HEARTBEAT_INTERVAL,
                )

                if message and message["type"] == "message":
                    count_data = json.loads(message["data"])
                    yield f"event: count\ndata: {json.dumps(count_data)}\n\n"

            except asyncio.TimeoutError:
                # Send heartbeat comment to keep connection alive
                yield ": heartbeat\n\n"

    except asyncio.CancelledError:
        logger.info(f"SSE unread count stream cancelled for user {user_id}")
        raise
    except Exception as e:
        logger.error(f"SSE unread count stream error for user {user_id}: {e}")
        yield f"event: error\ndata: {json.dumps({'error': 'stream_error'})}\n\n"
    finally:
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
        except Exception as e:
            logger.warning(f"Error closing count pubsub for user {user_id}: {e}")


async def publish_notification(user_id: uuid.UUID, notification_data: dict):
    """
    Publish a notification to a user's Redis channel.

    Args:
        user_id: The UUID of the user to notify
        notification_data: Dictionary containing notification data

    Returns:
        int: Number of subscribers that received the message
    """
    channel = f"notifications:{user_id}"

    try:
        result = await redis.publish(channel, json.dumps(notification_data))
        logger.info(
            f"Published notification to {channel}, {result} subscribers received"
        )
        return result
    except Exception as e:
        logger.error(f"Failed to publish notification to {channel}: {e}")
        raise


async def publish_unread_count(user_id: uuid.UUID, count: int):
    """
    Publish an unread count update to both notification and count channels.

    Publishes to:
    - notifications:{user_id} - for clients using the main notification stream
    - notifications:count:{user_id} - for clients using the dedicated count stream

    Args:
        user_id: The UUID of the user to notify
        count: The new unread notification count

    Returns:
        int: Total number of subscribers that received the message
    """
    count_data = {"event_type": "unread_count", "unread_count": count}

    try:
        # Publish to both channels
        notification_channel = f"notifications:{user_id}"
        count_channel = f"notifications:count:{user_id}"

        result1 = await redis.publish(notification_channel, json.dumps(count_data))
        result2 = await redis.publish(count_channel, json.dumps(count_data))

        logger.info(f"Published unread count {count} to user {user_id}")
        return result1 + result2
    except Exception as e:
        logger.error(f"Failed to publish unread count for user {user_id}: {e}")
        raise
