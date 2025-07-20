# надо релизовать интерфейс streamInterface

import streamInterface;
from streamImplementation import StreamImplementation

class StreamController:
    def __init__(self, streamer: StreamInterface):
        self.llm = llm
    
    def stream(self, prompt):
        streamInterface.stream(self.llm, prompt)
        
