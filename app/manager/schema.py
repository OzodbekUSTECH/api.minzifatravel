from pydantic import BaseModel
from typing import Optional
from datetime import datetime




# class FileSchema(BaseModel):
#     id: int
#     file_name: str
#     file_path: str


# class MessageSchema(BaseModel):
#     id: int
#     text: str = None
#     is_manager_message: bool
#     time: datetime
#     file: FileSchema = None

#     class Config:
#         orm_mode = True

# class ClientSchema(BaseModel):
#     id: int
#     full_name: str
#     phone_number: str
#     language: str
#     source: str
#     created_at: datetime
#     status: str
#     last_update: datetime
#     description: str = None
#     chat: list[MessageSchema] # Поле chat теперь необязательное

#     class Config:
#         orm_mode = True
class CreateClientSchema(BaseModel):
    full_name: Optional[str]
    phone_number: Optional[str]
    email: Optional[str]
    language: Optional[str]
    source: Optional[str]
class UpdateClientSchema(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str]
    language: Optional[str] = None
    source: Optional[str] = None
    

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

class ChangeOwnTaskSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    time_deadline: Optional[str] = None
    date_deadline: Optional[str] = None
    priority: Optional[str] = None

