from pydantic import BaseModel, Field, EmailStr, constr


class NewUser(BaseModel):
    name: str = Field(..., max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=10)


class ErrorMessage(BaseModel):
    message: str


class PlantUpdate(BaseModel):
    name: str
    howOftenWatering: int = Field(..., gt=0)
    waterVolume: float = Field(..., gt=0)
    light: constr(strict=True)


class LoginUser(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=10)