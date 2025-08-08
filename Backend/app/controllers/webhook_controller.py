from fastapi import APIRouter, Request, HTTPException, Depends, Path
from sqlalchemy.orm import Session
from app.models.session import get_db
from app.models.models import Chat, User
from app.policies.policies import generate_ai_response, stream_ai_response, save_message_to_chat
from app.dependencies.auth import get_current_active_user

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


@router.post("/chats/{chat_id}/stream")
async def stream_chat_response(
    chat_id: int = Path(...),
    request: Request = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Стриминговый ответ ИИ и сохранение в чат"""
    try:
        data = await request.json()
        prompt = data.get("prompt", "")

        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        # Сохраняем пользовательское сообщение
        save_message_to_chat(db, chat_id, "user", prompt)

        # Возвращаем стриминговый ответ
        return stream_ai_response(prompt)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
