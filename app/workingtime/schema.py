from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import time, date

class AllWorkTimeSchema(BaseModel):
    id: int
    staff_id: int
    full_name: str
    date: date
    start_time: time
    end_time: time
    

class WorkTimeSchema(BaseModel):
    id: int
    full_name: str
    start_time: time
    end_time: time

class WorkDateSchema(BaseModel):
    date: date
    staff: list[WorkTimeSchema]

class WorkTimeIn(BaseModel):
    id: int
    staff_id: int
    full_name: str
    start_time: time

    class Config:
        orm_mode = True

class WorkTimeOut(BaseModel):
    id: int
    staff_id: int
    full_name: str
    start_time: time
    end_time: time

class OwnWorkTime(BaseModel):
    id: int
    date: date
    start_time: time
    end_time: time

    class Config:
        orm_mode = True