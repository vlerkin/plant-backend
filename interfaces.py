from pydantic import BaseModel, Field, EmailStr


class NewUser(BaseModel):
    name: str = Field(..., max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=10)


class ErrorMessage(BaseModel):
    message: str

