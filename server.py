from datetime import datetime, timedelta
from pprint import pprint

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import Session, joinedload

from auth import get_password_hash
from config import Configuration
from models import User, Plant, WaterLog, FertilizerLog, PlantDisease
from interfaces import NewUser


app = FastAPI()
engine = create_engine(Configuration.connectionString, echo=True)
session = Session(engine)



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


# get user's plants
@app.get("/my-plants")
async def show_my_plants():
    user_id = 1
    user_plants = (session.query(Plant).filter_by(userId=user_id).all())
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