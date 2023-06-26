from pydantic import BaseModel
from typing import *
from datetime import datetime, date


class TokenSchema(BaseModel):
    access_token: str
    token_type: str

    class Config:
        orm_mode = True

class TokenData(BaseModel):
    email: str



class UserCreateSchema(BaseModel):
    full_name: str
    email: str
    password: str
    department: str
    role: str
    language: str

class RegUserSchemaResponse(BaseModel):
    id: int
    full_name: str
    email: str
    department: str
    role: str
    language: str
    status: str 
    amount_finished_clients:Optional[int]

    class Config:
        orm_mode = True


################################################################
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

    class Config:
        orm_mode = True

class Client(BaseModel):
    id: int
    full_name: str
    language: str
    source: str
    created_at: datetime
    status: str
    description: str = None
    chat: Optional[List[MessageSchema]] # Поле chat теперь необязательное

    class Config:
        orm_mode = True

class UserSchema(BaseModel):
    id: int
    full_name: str
    email: str
    department: str
    role: str
    language: str
    status: str 
    amount_finished_clients:Optional[int]
    clients: list[Client]

    class Config:
        orm_mode = True


##############################

class TaskSchema(BaseModel):
    id: int
    created_at: datetime
    created_by_id: int
    staff_id: int
    title: str
    importance: str
    status: str
    timer_deadline: str
    date_deadline: Optional[date]

    class Config:
        orm_mode = True


class CreateTaskSchema(BaseModel):
    title: str
    timer_deadline: Optional[str] = None
    date_deadline: Optional[date] = None
    importance: str
    staff_id: int