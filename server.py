from pprint import pprint

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import User, Plant
from interfaces import NewUser
from passlib.context import CryptContext

app = FastAPI()
engine = create_engine("postgresql://test@localhost:5432/test", echo=True)
session = Session(engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# password verification and hashing
def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# API
@app.get("/")
async def root():
    return {"message": "Hello World"}


# register a new user
@app.post("/register")
async def create_new_user(new_user: NewUser):
    password = get_password_hash(new_user.password)
    try:
        db_new_user = User(
            name=new_user.name,
            password=password,
            email=new_user.email,
        )
        session.add(db_new_user)
        session.commit()
        session.refresh(db_new_user)
        return new_user
    except ValidationError as error:
        raise HTTPException(status_code=400, detail=str(error))
    finally:
        session.close()


@app.get("/my-plants")
async def show_my_plants():
    user_id = 1
    user_plants = session.query(Plant).filter_by(userId=user_id).all()
    return user_plants
    session.close()