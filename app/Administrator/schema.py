from pydantic import BaseModel
from typing import *
from datetime import datetime, date
from fastapi import UploadFile


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
    avatar: Optional[str]
    full_name: str
    email: str
    department: str
    role: str
    language: str
    is_busy: bool 
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

class ClientSchema(BaseModel):
    id: int
    full_name: str
    language: str
    source: str
    created_at: datetime
    status: str
    last_update: datetime
    description: str = None
    chat: List[MessageSchema] # Поле chat теперь необязательное

    class Config:
        orm_mode = True

class UserSchema(BaseModel):
    id: int
    avatar: Optional[str]
    full_name: str
    email: str
    department: str
    role: str
    language: str
    is_busy: bool
    amount_finished_clients:Optional[int]
    clients: List[ClientSchema]

    class Config:
        orm_mode = True

class UserUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    language: Optional[str] = None

class UserUpdatePasswordSchema(BaseModel):
    old_password: str
    new_password: str

##############################

class TaskSchema(BaseModel):
    id: int
    created_at: datetime
    created_by_id: int
    assigned_to_id: Optional[int]
    title: str
    description: str
    priority: str
    percent: Optional[float]
    is_done: bool
    time_deadline: str
    date_deadline: str

    class Config:
        orm_mode = True


class CreateTaskSchema(BaseModel):
    assigned_to_id: int
    title: str
    description: str
    time_deadline: str
    date_deadline: str
    priority: str
    percent: float
    

from pydantic import BaseModel, Field
class UpdateTaskSchema(BaseModel):
    assigned_to_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    time_deadline: Optional[str] = None
    date_deadline: Optional[str] = None
    priority: Optional[str] = None
    percent: Optional[float] = None


#######################################