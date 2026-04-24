from abc import ABC, abstractmethod

from mistralai.client import Mistral
from pydantic import BaseModel


class BaseAgent(ABC):
    name: str
    system_prompt: str

    def __init__(self, client: Mistral) -> None:
        self.client = client

    @abstractmethod
    async def run(self, input: BaseModel) -> BaseModel: ...
