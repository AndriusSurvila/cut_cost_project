from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from app.container import Container
from app.services.api_model_service import CladeModelService
from app.contracts.stream_interface import LLMStreamInterface
from app.controllers.stream_controller import StreamController
from fastapi import stream_controller

container = Container()
container.bind(LLMStreamInterface, CladeModelService)
stream_controller = container.resolve(StreamController)

app = FastAPI()
app.include_router(stream_controller.router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

@app.post("/ask")
def ask(request: QuestionRequest):
    user_question = request.question.strip()

    step1_prompt = f"""
Detect the language of the question and translate it into English.
Return ONLY the translated English version, no comments.

Question: {user_question}
"""
    english_question = stream_controller.stream(step1_prompt)

    step2_prompt = f"""
Answer the following question in English, clearly and concisely:

{english_question}
"""
    english_answer = stream_controller.stream(step2_prompt)

    step3_prompt = f"""
The original question was: "{user_question}"
The answer in English is: "{english_answer}"
Detect the original language and translate the answer BACK into it.
Return ONLY the translated answer, with no extra text.
"""
    final_answer = stream_controller.stream(step3_prompt)

    return {"answer": final_answer}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)