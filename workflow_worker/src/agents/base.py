from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from mistralai.client import Mistral
from pydantic import BaseModel

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class BaseAgent(ABC, Generic[InputT, OutputT]):
    name: str

    def __init__(self, client: Mistral) -> None:
        self.client = client

    @abstractmethod
    async def run(self, params: InputT) -> OutputT: ...
