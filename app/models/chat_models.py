from pydantic import BaseModel


class ChatRequest(BaseModel):
    user_message: str


class ChatResponse(BaseModel):
    user_message: str
    response: str