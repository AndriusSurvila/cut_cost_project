# controllers/chat_controller.py

from fastapi import APIRouter, Path, HTTPException
from app.policies import stream_ai_response

router = APIRouter()

@router.post("/chats/{chat_id}/stream")
def stream(chat_id: int, request: dict):
    prompt = request.get("prompt", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    return stream_ai_response(prompt)
