from app.contracts.stream_interface import LLMStreamInterface
import requests
import os

class CladeModelService(LLMStreamInterface):
    def __init__(self):
        self.OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

    def predict(self, input_text: str) -> str:
        payload = {
            "model": "mistral",
            "prompt": input_text.strip(),
            "stream": False
        }
        try:
            response = requests.post(self.OLLAMA_URL, json=payload, timeout=90)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except requests.Timeout:
            return "[Error] Timeout from Ollama."
        except requests.RequestException as e:
            return f"[Error] Request failed: {str(e)}"

    def mode(self) -> str:
        return "api"