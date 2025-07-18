from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import uvicorn
import os

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

def ask_ollama(prompt: str) -> str:
    data = {
        "model": "mistral",
        "prompt": prompt.strip(),
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=data, timeout=90)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Ollama timeout")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {str(e)}")

@app.post("/ask")
def ask(request: QuestionRequest):
    user_question = request.question.strip()

    step1_prompt = f"""
Detect the language of the question and translate it into English.
Return ONLY the translated English version, no comments.

Question: {user_question}
"""
    english_question = ask_ollama(step1_prompt)

    step2_prompt = f"""
Answer the following question in English, clearly and concisely:

{english_question}
"""
    english_answer = ask_ollama(step2_prompt)

    step3_prompt = f"""
The original question was: "{user_question}"
The answer in English is: "{english_answer}"
Detect the original language and translate the answer BACK into it.
Return ONLY the translated answer, with no extra text.
"""
    final_answer = ask_ollama(step3_prompt)

    return {"answer": final_answer}