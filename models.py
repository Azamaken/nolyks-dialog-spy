from typing import Optional
from sqlmodel import SQLModel, Field


class Message(SQLModel, table=True):
    id: int = Field(primary_key=True)

    chat_id: int
    user_id: int

    from_username: str
    first_name: str

    type: str
    content: Optional[str] = None

    created_at: str


class File(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    file_name: str
    message_id: int