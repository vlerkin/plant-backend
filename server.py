import random
import uuid
from datetime import datetime, timedelta
from pprint import pprint

import boto3
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from pydantic import ValidationError

from sqlalchemy import create_engine, desc, update
from sqlalchemy.orm import Session

from auth import get_password_hash, oauth2_scheme, get_user, authenticate_user, create_access_token
from config import Configuration
from models import User, Plant, WaterLog, FertilizerLog, PlantDisease, Disease
from interfaces import NewUser, LoginUser, UserProfile, MyPlants, PlantUpdate, UserUpdate, CreateFertilizing, \
    PlantDiseaseCreate, LightEnum, LocationEnum
from typing import Annotated, List

app = FastAPI()
engine = create_engine(Configuration.connection_string, echo=True)
session = Session(engine)
origins = [
    "http://localhost:3000",
    "http://localhost:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

s3 = boto3.client(
    "s3",
    aws_access_key_id=Configuration.aws_access_key_id,
    aws_secret_access_key=Configuration.aws_secret_access_key,
    region_name=Configuration.aws_region_name
)

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, Configuration.secret_key, algorithms=[Configuration.algorithm])
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
@app.get("/my-plants", response_model=List[MyPlants])
async def show_my_plants(user: User = Depends(get_current_user)):
    user_plants = (session.query(Plant).filter_by(userId=user.id).all())
    return user_plants


# create a plant
@app.post("/my-plants")
async def create_plant(new_plant: PlantUpdate, user: User = Depends(get_current_user)):
    try:
        db_new_plant = Plant(name=new_plant.name,
                             photo=new_plant.photo,
                             howOftenWatering=new_plant.howOftenWatering,
                             waterVolume=new_plant.waterVolume,
                             light=new_plant.light,
                             location=new_plant.location,
                             comment=new_plant.comment,
                             species=new_plant.species,
                             userId=user.id)
        session.add(db_new_plant)
        session.commit()
        return new_plant
    except ValidationError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/upload/{category}")
async def upload_photo(file: UploadFile, category: str, user: User = Depends(get_current_user)):
    filename = str(user.id) + "/" + category + "/" + file.filename.lower()
    s3.upload_fileobj(file.file, Configuration.aws_bucket_name, filename)
    return {'filename': filename, 'user_id': user.id}


# get user profile
@app.get("/me", response_model=UserProfile)
async def show_me(user: User = Depends(get_current_user)):
    return user


@app.patch("/me")
async def edit_profile(user_info: UserUpdate, user: User = Depends(get_current_user)):
    user_id = user.id
    user_to_update = session.query(User).filter_by(id=user_id).one()
    # take existing photo
    photo = user.photo
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")
    # if user provided new photo, update photo variable to use for patching
    if user_info.photo:
        photo = user_info.photo
    # if user provided new password, check it and hash before updating
    if user_info.password and get_password_hash(user_info.password) != user_to_update.password:
        hashed_password = get_password_hash(user_info.password)
        user_update = {User.name: user_info.name,
                       User.email: user_info.email,
                       User.photo: photo,
                       User.password: hashed_password
                       }
        session.execute(update(User).where(User.id == user_id).values(user_update))
        session.commit()
        return {"message": "user updated"}
    # if user did not provide a new password update user with the existing one
    else:
        user_update = {User.name: user_info.name,
                       User.email: user_info.email,
                       User.photo: photo,
                       User.password: user_to_update.password}
        session.execute(update(User).where(User.id == user_id).values(user_update))
        session.commit()
        return {"message": "user updated"}


# get a plant's info
@app.get("/my-plants/{plant_id}")
async def get_plant(plant_id: int, user: User = Depends(get_current_user)):
    user_id = user.id
    thirty_days_ago = datetime.now() - timedelta(days=30)
    ninety_days_ago = datetime.now() - timedelta(days=90)
    plant_of_user = session.query(Plant).filter_by(userId=user_id, id=plant_id).one()
    plant_watering = session.query(WaterLog).filter(WaterLog.plantId == plant_id, WaterLog.dateTime >= thirty_days_ago).all()
    plant_fertilizing = session.query(FertilizerLog).filter(FertilizerLog.plantId == plant_id, FertilizerLog.dateTime >= thirty_days_ago).all()
    plant_disease = session.query(PlantDisease).filter(PlantDisease.plantId == plant_id, PlantDisease.startDate >= ninety_days_ago).order_by(desc(PlantDisease.endDate)).all()
    if not plant_of_user:
        raise HTTPException(status_code=404, detail="Plant not found")
    return {"info": plant_of_user, "photo": plant_of_user.photo_url, "watering_log": plant_watering, "fertilizing_log": plant_fertilizing, "disease_log": plant_disease}


# delete a plant
@app.delete("/my-plants/{plant_id}")
async def delete_plant(plant_id: int, user: User = Depends(get_current_user)):
    user_id = user.id
    plant_to_delete = session.query(Plant).filter(Plant.userId == user_id, Plant.id == plant_id).one()
    if not plant_to_delete:
        raise HTTPException(status_code=404, detail="Plant not found")
    session.delete(plant_to_delete)
    session.commit()
    return {"message": "Plant deleted"}


@app.patch("/my-plants/{plant_id}")
async def update_plant(plant_id: int, plant_info: PlantUpdate, user: User = Depends(get_current_user)):
    # get user id from auth to add it later to a plant info to update a plant
    user_id = user.id
    # find a plant with the requested id, if it exists, check if this plant belongs to the authorized user
    plant_to_update = session.query(Plant).filter_by(id=plant_id).one()
    if not plant_to_update:
        raise HTTPException(status_code=404, detail="Plant not found")
    if plant_to_update.userId != user_id:
        raise HTTPException(status_code=401, detail="You are not authorized")
    location = plant_to_update.location
    photo = plant_to_update.photo
    comment = plant_to_update.comment
    species = plant_to_update.species
    if plant_info.location:
        location = plant_info.location
    if plant_info.photo:
        photo = plant_info.photo
    if plant_info.comment:
        comment = plant_info.comment
    if plant_info.species:
        species = plant_info.species
    plant_update = {Plant.name: plant_info.name,
                    Plant.howOftenWatering: int(plant_info.howOftenWatering),
                    Plant.waterVolume: float(plant_info.waterVolume),
                    Plant.light: plant_info.light,
                    Plant.location: location,
                    Plant.photo: photo,
                    Plant.comment: comment,
                    Plant.species: species,
                    Plant.userId: user_id}
    session.execute(update(Plant).where(Plant.id == plant_id).values(plant_update))
    session.commit()
    return {"message": "plant updated"}


@app.post("/my-plants/{plant_id}/watering")
async def create_watering(plant_id: int, user: User = Depends(get_current_user)):
    user_id = user.id
    # find a plant with the requested id, if it exists, check if this plant belongs to the authorized user
    plant_to_update = session.query(Plant).filter_by(id=plant_id).one()
    if not plant_to_update:
        raise HTTPException(status_code=404, detail="Plant not found")
    if plant_to_update.userId != user_id:
        raise HTTPException(status_code=401, detail="You are not authorized")

    try:
        db_new_watering = WaterLog(dateTime=datetime.now(),
                                   waterVolume=plant_to_update.waterVolume,
                                   plantId=plant_to_update.id)
        session.add(db_new_watering)
        session.commit()
        return {"message": "plant watered"}
    except ValidationError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/my-plants/{plant_id}/fertilizing")
async def create_fertilizing(plant_id: int, fertilizing_info: CreateFertilizing, user: User = Depends(get_current_user)):
    user_id = user.id
    # find a plant with the requested id, if it exists, check if this plant belongs to the authorized user
    plant_to_update = session.query(Plant).filter_by(id=plant_id).one()
    if not plant_to_update:
        raise HTTPException(status_code=404, detail="Plant not found")
    if plant_to_update.userId != user_id:
        raise HTTPException(status_code=401, detail="You are not authorized")
    try:
        db_new_fertilizing = FertilizerLog(dateTime=datetime.now(),
                                           quantity=fertilizing_info.quantity,
                                           type=fertilizing_info.type,
                                           plantId=plant_to_update.id)
        session.add(db_new_fertilizing)
        session.commit()
        return {"message": "added fertilizing to log"}
    except ValidationError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/my-plants/{plant_id}/plant-disease")
async def add_plant_disease(plant_id: int, disease_info: PlantDiseaseCreate, user: User = Depends(get_current_user)):
    user_id = user.id
    # find a plant with the requested id, if it exists, check if this plant belongs to the authorized user
    plant_to_update = session.query(Plant).filter_by(id=plant_id).one()
    if not plant_to_update:
        raise HTTPException(status_code=404, detail="Plant not found")
    if plant_to_update.userId != user_id:
        raise HTTPException(status_code=401, detail="You are not authorized")
    # check if requested disease with the provided id exists
    requested_disease = session.query(Disease).filter_by(id=disease_info.diseaseId).one()
    if not requested_disease:
        raise HTTPException(status_code=404, detail="Disease not found")
    # check if user has created the same plant_disease for the past day for the same plant and disease
    yesterday = datetime.now() - timedelta(days=1)
    plant_disease = session.query(PlantDisease).filter(PlantDisease.plantId == plant_id,
                                                       PlantDisease.diseaseId == disease_info.diseaseId,
                                                       PlantDisease.startDate == disease_info.startDate,
                                                       PlantDisease.endDate >= yesterday).all()
    if plant_disease:
        print("You already added this disease")
        return None
    try:
        db_new_plant_disease = PlantDisease(plantId=plant_id,
                                            diseaseId=disease_info.diseaseId,
                                            startDate=disease_info.startDate,
                                            endDate=disease_info.endDate,
                                            treatment=disease_info.treatment,
                                            comment=disease_info.comment)
        session.add(db_new_plant_disease)
        session.commit()
        return disease_info
    except ValidationError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/all-diseases")
async def all_diseases():
    diseases = session.query(Disease).all()
    return diseases
