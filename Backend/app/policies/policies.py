from services.api_model_service import CladeModelService

llm = CladeModelService()

def generate_ai_response(prompt: str) -> str:
    return llm.predict(prompt)