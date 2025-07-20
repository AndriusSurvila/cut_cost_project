from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.policies import generate_ai_response
from app.models.session import get_db
from sqlalchemy.orm import Session

router = APIRouter()

class StreamRequest(BaseModel):
    prompt: str

@router.post("/webhook")
def handle_webhook(request: StreamRequest, db: Session = Depends(get_db)):
    answer = generate_ai_response(request.prompt, db)
    return {"answer": answer}

@router.post("/chats/{chat_id}/stream")
def stream(chat_id: int, request: StreamRequest, db: Session = Depends(get_db)):
    def token_stream():
        response = generate_ai_response(request.prompt, db)
        for word in response.split():
            yield word + " "
    return StreamingResponse(token_stream(), media_type="text/plain")
