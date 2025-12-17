from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.utils.redis import notification_streamer

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/{user_id}")
async def notifications(user_id: str):
    return StreamingResponse(
        notification_streamer(user_id), media_type="text/event-stream"
    )
