from fastapi import APIRouter, Request, HTTPException
from app.policies import generate_ai_response, stream_ai_response
from starlette.responses import StreamingResponse

router = APIRouter()

@router.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
        stream = data.get("stream", False)

        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        if stream:
            return stream_ai_response(prompt)
        else:
            response = generate_ai_response(prompt)
            return {"response": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))