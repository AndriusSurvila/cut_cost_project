from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import requests
import uvicorn

app = FastAPI()

OLLAMA_URL = "http://localhost:11434/api/generate"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ask")
def ask(question: str = Body(..., embed=True)):
    data = {
        "model": "mistral",
        "prompt": question,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=data, timeout=60)
        response.raise_for_status()

        result = response.json()
        answer = result.get("response", "No response")
        return {"answer": answer}

    except requests.RequestException as e:
        return {"error": f"Connection error: {str(e)}"}

    except Exception as e:
        return {"error": f"Внутренняя ошибка сервера: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run("main:app")