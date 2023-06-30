from fastapi import APIRouter, HTTPException, Depends, status
from database.db import get_db
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from .utils import *
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix='/login',
    tags = ['Login']
)


@router.post("/", response_model=TokenSchema)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"id": user.id, "full_name": user.full_name, "email": user.email, "department": user.department, "role": user.role}
    )
    response = TokenSchema( access_token=access_token, token_type="bearer")
    return response

@router.get('/get_user/me', name="get own data", response_model=UserSchema)
async def get_all_staff(current_user=Depends(get_current_user), db: Session = Depends(get_db)):

    

    clients_response = []
    for client in current_user.clients:
        chat_response = []
        for message in client.messages:
            file_data = None
            if message.file:
                file_data = FileSchema(
                    id=message.file.id,
                    file_name=message.file.filename,
                    file_path=message.file.filepath
                )
            chat_data = MessageSchema(
                id=message.id,
                text=message.text,
                is_manager_message=message.is_manager_message,
                time = message.timestamp,
                file = file_data
            )
            chat_response.append(chat_data)
        client_data = ClientSchema(
            id = client.id,
            full_name=client.full_name,
            phone_number=client.phone_number,
            language=client.language,
            source=client.source,
            created_at=client.created_at,
            status=client.status,
            last_update=client.last_manager_update,
            description=client.description,
            chat= chat_response
        )
        clients_response.append(client_data)

    response = UserSchema(
        id=current_user.id,
        avatar=current_user.avatar,
        full_name=current_user.full_name,
        email=current_user.email,
        department=current_user.department,
        role=current_user.role,
        language=current_user.language,
        is_busy=current_user.is_busy,
        amount_finished_clients=current_user.amount_finished_clients,
        clients = clients_response
    )

    return response

@router.put('/change/password', name="change own password")
async def change_own_password(old_password: str, new_password: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if verify_password(old_password, current_user.password):
        new_hashed_password = pwd_context.hash(new_password)
        current_user.password = new_hashed_password
        db.commit()
        return {"message": "Пароль был успешно изменен"}
    else:
        raise HTTPException(status_code=400, detail="Неверный пароль")