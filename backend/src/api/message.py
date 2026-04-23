from fastapi import APIRouter

from src.schemas.message import MessageRequest, MessageResponse

router = APIRouter()

HARDCODED_REPLY = "Hello from the backend! You said: {input}"


@router.post("/message", response_model=MessageResponse)
def post_message(body: MessageRequest) -> MessageResponse:
    return MessageResponse(message=HARDCODED_REPLY.format(input=body.input))
