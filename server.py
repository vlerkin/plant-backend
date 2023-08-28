from pprint import pprint

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import User
from interfaces import NewUser

app = FastAPI()
engine = create_engine("postgresql://test@localhost:5432/test", echo=True)
session = Session(engine)


@app.get("/")
async def root():
    return {"message": "Hello World"}


# register a new user
@app.post("/register")
async def root(new_user: NewUser):
    try:
        db_new_user = User(
            name=new_user.name,
            password=new_user.password,
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


