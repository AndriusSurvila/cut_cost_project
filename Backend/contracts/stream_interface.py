from abc import ABC, abstractmethod

class LLMStreamInterface(ABC):
    @abstractmethod
    def predict(self, input_text: str) -> str:
        """Предсказание на основе входного текста"""
        pass

    @abstractmethod
    def mode(self) -> str:
        """Режим модели: local или api"""
        pass
