from fastapi import APIRouter, HTTPException, Depends, status
from database.db import get_db
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from app.utils import *
from sqlalchemy.exc import IntegrityError
from app.manager.schema import *
router = APIRouter(
    prefix='/api/v1',
    tags = ['Lead'],
    dependencies=[Depends(get_current_user)]
)

@router.put('/lead/{lead_id}', name='update lead data', response_model = LeadSchema)
async def update_lead_data(lead_id: int, lead: UpdateClientSchema, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    db_lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    
    if lead.full_name is not None:
        db_lead.full_name = lead.full_name
    if lead.phone_number is not None:
        db_lead.phone_number = lead.phone_number
    if lead.email is not None:
        db_lead.email = lead.email
    if lead.language is not None:
        db_lead.language = lead.language
    if lead.source is not None:
        db_lead.source = lead.source
    
    db.commit()
    db.refresh(db_lead)

    return db_lead