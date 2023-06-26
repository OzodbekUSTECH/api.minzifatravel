from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from app import models
from database.db import get_db
from sqlalchemy import desc
import asyncio
from app.utils import *
from pyrogram import types
import io
from .schema import *


router = APIRouter(
    prefix='/workingtime',
    tags = ['Working Time'],
    dependencies=[Depends(get_current_user)],
)

def get_current_date():
    return datetime.now().date()
def get_current_time():
    return datetime.now().time()

@router.post("/user/sigin", name='Create a start time for a staff', response_model = WorkTimeIn)
def create_time_tracking(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    current_time: datetime = Depends(get_current_time),
    current_date: datetime = Depends(get_current_date),
):
  
    has_workdate = db.query(models.WorkTime).filter(models.WorkTime.staff == current_user, models.WorkTime.date == current_date).first()
    if has_workdate:
        response = WorkTimeIn(
            id=has_workdate.id,
            staff_id = has_workdate.staff_id,
            full_name=has_workdate.staff.full_name,
            start_time=has_workdate.start_time
        )
        return response

    starting_time = models.WorkTime(
        staff=current_user,
        start_time=current_time,
        date=current_date
    )

    db.add(starting_time)
    db.commit()

    response = WorkTimeIn(
        id=starting_time.id,
        staff_id = starting_time.staff_id,
        full_name=starting_time.staff.full_name,
        start_time=starting_time.start_time
    )
    return response


@router.put("/user/signout",name='Create an end time for a staff', response_model = WorkTimeOut)
def update_time_tracking(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    current_time: datetime = Depends(get_current_time)
):
    worktime = db.query(models.WorkTime).filter(models.WorkTime.staff == current_user).first()

    if not worktime:
        raise HTTPException(status_code=404, detail="WorkTime not found")


    worktime.end_time = current_time
    db.commit()
    response = WorkTimeOut(
        id = current_user.id,
        staff_id = current_user.id,
        full_name = current_user.full_name,
        start_time = worktime.start_time,
        end_time = worktime.end_time
    )
    return response




