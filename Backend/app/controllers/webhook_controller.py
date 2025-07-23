from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.session import get_db
from app.policies.policies import generate_ai_response, stream_ai_response

router = APIRouter()

@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    """Webhook для обработки внешних запросов"""
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
        stream = data.get("stream", False)

        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        if stream:
            return stream_ai_response(prompt)
        else:
            response = generate_ai_response(prompt, db)
            return {"response": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))