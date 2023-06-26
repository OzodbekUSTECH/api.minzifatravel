from fastapi import APIRouter, HTTPException, Depends, status
from database.db import get_db
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from app.utils import *
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix='/administrator',
    tags = ['Administrator']
)


@router.post('/registration', summary="Create a new user", response_model=RegUserSchemaResponse)
async def register(user: UserCreateSchema,current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "God":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")

    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        full_name=user.full_name,
        email=user.email,
        department=user.department,
        role=user.role,
        language=user.language
    )
    db_user.password = hashed_password
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует.")


    # response = RegUserSchemaResponse(
    #     id=db_user.id,
    #     full_name=db_user.full_name,
    #     email=db_user.email,
    #     department=db_user.department,
    #     role=db_user.role,
    #     language=db_user.language
    # )
    return db_user



@router.get('/get_all_staff', name="get list of staff with their clients and full chats", response_model=list[UserSchema])
async def get_all_staff(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "God":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")

    all_staff = db.query(models.User).order_by('id').all()
    response = []
    for staff in all_staff:
        clients = []
        for client in staff.clients:
            messages_response = []
            for message in client.messages:
                file_data = None
                if message.file:
                    file_data = FileSchema(
                        id=message.file.id,
                        file_name=message.file.filename,
                        file_path=message.file.filepath
                    )
                message_data = MessageSchema(
                    id=message.id,
                    text=message.text,
                    is_manager_message=message.is_manager_message,
                    time=message.timestamp,
                    file = file_data
                )
                messages_response.append(message_data)
            client_data = Client(
                id=client.id,
                full_name=client.full_name,
                language=client.language,
                source=client.source,
                created_at=client.created_at,
                status=client.status,
                description=client.description,
                chat = messages_response
            )
            clients.append(client_data)

        staff_data = UserSchema(
            id=staff.id,
            full_name=staff.full_name,
            email=staff.email,
            department=staff.department,
            role=staff.role,
            language=staff.language,
            status=staff.status,
            amount_finished_clients=staff.amount_finished_clients,
            clients=clients 
        )
        response.append(staff_data)

    return response


@router.get('/get_all_tasks', response_model=List[TaskSchema])
async def get_all_tasks(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "God":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")
    all_tasks = db.query(models.Task).order_by(models.Task.id).all()
    return all_tasks


@router.post('/create_task', response_model=TaskSchema)
async def create_task(task: CreateTaskSchema, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.department != "God":
        raise HTTPException(status_code=403, detail="Недостаточно прав доступа.")


    db_task = models.Task(
        title=task.title,
        timer_deadline=task.timer_deadline,
        date_deadline=task.date_deadline,
        importance=task.importance,
        created_by=current_user,  # Use the retrieved User instance
        staff_id=task.staff_id
    )
    db.add(db_task)
    db.commit()

    
    return db_task

from app.workingtime.schema import *
#working times of managers
@router.get("/workingtime/dates_all", name='get all dates and their staff with working time', response_model=list[WorkDateSchema])
def get_all_users_by_dates(db: Session = Depends(get_db)):

    users = db.query(models.WorkTime).order_by(models.WorkTime.date, models.WorkTime.staff_id).all()

    result = {}
    for user in users:
        date_str = user.date  

        user_data = WorkTimeSchema(
            id=user.staff.id,
            full_name=user.staff.full_name,
            start_time=user.start_time,
            end_time=user.end_time,
        )
        if date_str in result:
            result[date_str].append(user_data)
        else:
            result[date_str] = [user_data]
    
    response = []
    for date_str, staff in result.items():
        date_data = WorkDateSchema(date=date_str, staff=staff)
        response.append(date_data)
    return response


@router.get("/workingtime/dates/{date}", name='get all staff with working time for a specific date', response_model=List[AllWorkTimeSchema])
def get_all_users_by_date(date: date, db: Session = Depends(get_db)):

    users = db.query(models.WorkTime).filter(models.WorkTime.date == date).order_by(models.WorkTime.id).all()

    response = []
    for user in users:
        user_data = AllWorkTimeSchema(
            id=user.id,
            staff_id=user.staff.id,
            full_name=user.staff.full_name,
            date=user.date,
            start_time=user.start_time,
            end_time=user.end_time
        )
        response.append(user_data)

    return response

@router.get("/workingtime/range/dates", name='get all staff with working time for a range of dates', response_model=List[AllWorkTimeSchema])
def get_all_users_by_range(start_date: date, end_date: Optional[date] = None, db: Session = Depends(get_db)):

    query = db.query(models.WorkTime).filter(models.WorkTime.date >= start_date)

    if end_date:
        query = query.filter(models.WorkTime.date <= end_date)

    users = query.order_by('id').all()
    response = []
    for user in users:
        user_data = AllWorkTimeSchema(
            id=user.id,
            staff_id=user.staff.id,
            full_name=user.staff.full_name,
            date=user.date,
            start_time=user.start_time,
            end_time=user.end_time
        )
        response.append(user_data)

    return response