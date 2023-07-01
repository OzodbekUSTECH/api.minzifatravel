from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import time, date

class AllWorkTimeSchema(BaseModel):
    id: int
    staff_id: int
   
    date: date
    start_time: time
    end_time: time
    
    class Config:
        orm_mode = True



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