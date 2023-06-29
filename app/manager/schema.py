from pydantic import BaseModel
from typing import Optional
from datetime import datetime




class FileSchema(BaseModel):
    id: int
    file_name: str
    file_path: str


class MessageSchema(BaseModel):
    id: int
    text: str = None
    is_manager_message: bool
    time: datetime
    file: FileSchema = None

class ClientSchema(BaseModel):
    id: int
    chat_id: int
    full_name: str
    language: str
    source: str
    status: str
    last_manager_update: datetime
    description: str = None
    chat: list[MessageSchema]

    class Config:
        orm_mode = True

class ClientStatusChange(BaseModel):
    message: str
    details: dict


######################################
class OwnTaskSchema(BaseModel):
    id: int
    created_at: datetime
    title: str
    description: str
    priority: str
    is_done: bool
    time_deadline: str
    date_deadline: str

    class Config:
        orm_mode = True


class CreateOwnTask(BaseModel):
    title: str
    description: str
    time_deadline: str
    date_deadline: str
    priority: str
