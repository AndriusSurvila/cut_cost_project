# services/policies.py

import requests
from fastapi import HTTPException
from starlette.responses import StreamingResponse
import os

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

def stream_ai_response(prompt: str):
    data = {
        "model": "mistral",
        "prompt": prompt.strip(),
        "stream": True
    }

    try:
        response = requests.post(OLLAMA_URL, json=data, stream=True, timeout=90)
        response.raise_for_status()

        def generate():
            for line in response.iter_lines():
                if line:
                    yield line.decode("utf-8") + "\n"

        return StreamingResponse(generate(), media_type="text/plain")

    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Ollama timeout")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {str(e)}")
