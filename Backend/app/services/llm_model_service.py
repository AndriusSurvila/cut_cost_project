from gpt4free import you

def ask_gpt(prompt: str) -> str:
    """
    Отправляет запрос в бесплатный GPT (you.com API через gpt4free)
    и возвращает текст ответа.
    """
    try:
        response = you.Completion.create(
            prompt=prompt,
            detailed=True,
        )
        return response.text
    except Exception as e:
        return f"Ошибка при запросе к GPT: {e}"