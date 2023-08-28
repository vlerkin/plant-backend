from datetime import datetime, timedelta
from pprint import pprint

from fastapi import FastAPI, Depends, HTTPException, status
from jose import jwt, JWTError
from pydantic import ValidationError

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import Session

from auth import get_password_hash, oauth2_scheme, get_user, authenticate_user, create_access_token
from config import Configuration
from models import User, Plant, WaterLog, FertilizerLog, PlantDisease
from interfaces import NewUser, LoginUser
from typing import Annotated


app = FastAPI()
engine = create_engine(Configuration.connectionString, echo=True)
session = Session(engine)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, Configuration.secretKey, algorithms=[Configuration.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(session, email)
    if user is None:
        raise credentials_exception
    return user


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


# log in a user
@app.post("/login")
async def login_user(user_to_login: LoginUser):
    user = authenticate_user(session, user_to_login.email, user_to_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email}
    )
    return {"access_token": access_token, "token_type": "bearer"}


# get user's plants
@app.get("/my-plants")
async def show_my_plants(user: Annotated[User, Depends(get_current_user)]):
    user_plants = (session.query(Plant).filter_by(userId=user.id).all())
    return user_plants


# get a plant's info
@app.get("/my-plants/{plant_id}")
async def get_plant(plant_id: int):
    user_id = 1
    thirty_days_ago = datetime.now() - timedelta(days=30)
    ninety_days_ago = datetime.now() - timedelta(days=90)
    plant_of_user = session.query(Plant).filter_by(userId=user_id, id=plant_id).one()
    plant_watering = session.query(WaterLog).filter(WaterLog.plantId == plant_id, WaterLog.dateTime >= thirty_days_ago).all()
    plant_fertilizing = session.query(FertilizerLog).filter(FertilizerLog.plantId == plant_id, FertilizerLog.dateTime >= thirty_days_ago).all()
    plant_disease = session.query(PlantDisease).filter(PlantDisease.plantId == plant_id, PlantDisease.startDate >= ninety_days_ago).order_by(desc(PlantDisease.endDate)).all()
    if not plant_of_user:

        raise HTTPException(status_code=404, detail="Plant not found")
    return {"info": plant_of_user, "watering_log": plant_watering, "fertilizing_log": plant_fertilizing, "disease_log": plant_disease}


# delete a plant
@app.delete("/my-plants/{plant_id}")
async def delete_plant(plant_id: int):
    user_id = 1
    plant_to_delete = session.query(Plant).filter(Plant.userId == user_id, Plant.id == plant_id).one()
    if not plant_to_delete:
        raise HTTPException(status_code=404, detail="Plant not found")
    session.delete(plant_to_delete)
    session.commit()
    return {"message": "Plant deleted"}


@app.patch("/my-plants/{plant_id}")
async def update_plant(plant_id: int, plant_info):
    user_id = 1