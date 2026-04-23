from pydantic import BaseModel


class MessageRequest(BaseModel):
    input: str


class MessageResponse(BaseModel):
    message: str
