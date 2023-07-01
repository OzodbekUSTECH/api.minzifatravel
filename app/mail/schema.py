from pydantic import BaseModel


class EmailSchema(BaseModel):
    message: str