from contracts.stream_interface import LLMStreamInterface

class StreamController:
    def __init__(self, streamer: LLMStreamInterface):
        self.llm = streamer

    def stream(self, prompt: str) -> str:
        return self.llm.predict(prompt)