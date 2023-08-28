from datetime import datetime, timedelta
from pprint import pprint

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import Session, joinedload
from models import User, Plant, WaterLog, FertilizerLog, PlantDisease
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


# get user's plants
@app.get("/my-plants")
async def show_my_plants():
    user_id = 1
    user_plants = (session.query(Plant).filter_by(userId=user_id).all())
    return user_plants
    session.close()


# get a plant's info
@app.get("/my-plants/{plant_id}")
async def get_plant(plant_id: int):
    user_id = 1
    thirty_days_ago = datetime.now() - timedelta(days=30)
    ninety_days_ago = datetime.now() - timedelta(days=90)
    plant_of_user = session.query(Plant).filter_by(userId=user_id, id=plant_id).first()
    plant_watering = session.query(WaterLog).filter(WaterLog.plantId == plant_id, WaterLog.dateTime >= thirty_days_ago).all()
    plant_fertilizing = session.query(FertilizerLog).filter(FertilizerLog.plantId == plant_id, FertilizerLog.dateTime >= thirty_days_ago).all()
    plant_disease = session.query(PlantDisease).filter(PlantDisease.plantId == plant_id, PlantDisease.startDate >= ninety_days_ago).order_by(desc(PlantDisease.endDate)).all()
    if not plant_of_user:
        session.close()
        raise HTTPException(status_code=404, detail="Plant not found")
    return {"info": plant_of_user, "watering_log": plant_watering, "fertilizing_log": plant_fertilizing, "disease_log": plant_disease}
    session.close()