from pydantic import BaseModel


class ChatRequest(BaseModel):
    user_message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    user_message: str
    response: str
    session_id: str
