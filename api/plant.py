from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.exc import NoResultFound

from auth import get_current_user
from config import session
from interfaces import MyPlants, PlantUpdate, PlantIndividualInfo, CreateFertilizing, PlantDiseaseCreate, ArrayId, \
    WateringLog, AuthUser, EndDateDiseaseUpdate
from models import Plant, WaterLog, FertilizerLog, PlantDisease, Disease
from pydantic import ValidationError

from services.plant import get_user_plant_by_id, get_last_plant_watering, get_last_plant_fertilizing, get_plant_diseases

router = APIRouter()


# get user's plants
@router.get("/my-plants", response_model=List[MyPlants])
async def show_my_plants(user: AuthUser = Depends(get_current_user)):
    user_plants = (session.query(Plant).filter_by(userId=user.id).all())
    return user_plants


# create a plant
@router.post("/my-plants")
async def create_plant(new_plant: PlantUpdate, user: AuthUser = Depends(get_current_user)):
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
    finally:
        if session.in_transaction():
            session.rollback()


# get a plant's info
@router.get("/my-plants/{plant_id}", response_model=PlantIndividualInfo)
async def get_plant(plant_id: int, user: AuthUser = Depends(get_current_user)):
    plant_of_user = get_user_plant_by_id(user.id, plant_id)
    if not plant_of_user:
        raise HTTPException(status_code=404, detail="Plant not found")

    plant_watering = get_last_plant_watering(plant_id)
    plant_fertilizing = get_last_plant_fertilizing(plant_id)
    plant_diseases = get_plant_diseases(plant_id, 3)

    return {"info": plant_of_user,
            "watering_log": plant_watering,
            "fertilizing_log": plant_fertilizing,
            "disease_log": plant_diseases}


# delete a plant
@router.delete("/my-plants/{plant_id}")
async def delete_plant(plant_id: int, user: AuthUser = Depends(get_current_user)):
    try:
        plant_to_delete = get_user_plant_by_id(user.id, plant_id)
        if not plant_to_delete:
            raise HTTPException(status_code=404, detail="Plant not found")
        session.delete(plant_to_delete)
        session.commit()
        return {"message": "Plant deleted"}
    finally:
        if session.in_transaction():
            session.rollback()

@router.patch("/my-plants/{plant_id}")
async def update_plant(plant_id: int, plant_info: PlantUpdate, user: AuthUser = Depends(get_current_user)):
    try:
        # find a plant with the requested id, if it exists, check if this plant belongs to the authorized user
        plant_to_update = get_user_plant_by_id(user.id, plant_id)
        if not plant_to_update:
            raise HTTPException(status_code=404, detail="Plant not found")
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
                        Plant.userId: user.id}
        session.execute(update(Plant).where(Plant.id == plant_id).values(plant_update))
        session.commit()
        return {"message": "plant updated"}
    finally:
        if session.in_transaction():
            session.rollback()

@router.post("/my-plants/{plant_id}/watering", response_model=WateringLog)
async def create_watering(plant_id: int, user: AuthUser = Depends(get_current_user)):
    # find a plant with the requested id, if it exists, check if this plant belongs to the authorized user
    plant_to_update = get_user_plant_by_id(user.id, plant_id)
    if not plant_to_update:
        raise HTTPException(status_code=404, detail="Plant not found")

    try:
        db_new_watering = WaterLog(dateTime=datetime.now(),
                                   waterVolume=plant_to_update.waterVolume,
                                   plantId=plant_to_update.id)
        session.add(db_new_watering)
        session.commit()
        return db_new_watering
    except ValidationError as error:
        raise HTTPException(status_code=400, detail=str(error))
    finally:
        if session.in_transaction():
            session.rollback()


@router.post("/my-plants/watering")
async def water_several_plants(plant_ids: ArrayId, user: AuthUser = Depends(get_current_user)):
    if len(plant_ids.ids) == 0:
        raise HTTPException(status_code=400, detail="No plant ids")

    plants = session.query(Plant).filter(Plant.id.in_(plant_ids.ids), Plant.userId == user.id).all()
    # if plants has lower number of ids then some plants do not belong to an authorized user
    # or we have an edge case with non-unique ids
    if len(plants) != len(plant_ids.ids):
        raise HTTPException(status_code=400, detail="Bad request")
    try:
        for plant in plants:
            session.add(
                WaterLog(dateTime=datetime.now(),
                         waterVolume=plant.waterVolume,
                         plantId=plant.id)
            )
        session.commit()
        return {"message": "Plants watered"}
    finally:
        if session.in_transaction():
            session.rollback()


@router.post("/my-plants/{plant_id}/fertilizing")
async def create_fertilizing(plant_id: int, fertilizing_info: CreateFertilizing, user: AuthUser = Depends(get_current_user)):
    # find a plant with the requested id, if it exists, check if this plant belongs to the authorized user
    plant_to_update = get_user_plant_by_id(user.id, plant_id)
    if not plant_to_update:
        raise HTTPException(status_code=404, detail="Plant not found")
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
    finally:
        if session.in_transaction():
            session.rollback()


@router.post("/my-plants/{plant_id}/plant-disease")
async def add_plant_disease(plant_id: int, disease_info: PlantDiseaseCreate, user: AuthUser = Depends(get_current_user)):
    if disease_info.startDate.astimezone() > datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail='Disease cannot start in the future')
    # find a plant with the requested id, if it exists, check if this plant belongs to the authorized user
    plant_to_update = get_user_plant_by_id(user.id, plant_id)
    if not plant_to_update:
        raise HTTPException(status_code=404, detail="Plant not found")
    # check if requested disease with the provided id exists
    try:
        requested_disease = session.query(Disease).filter_by(id=disease_info.diseaseId).one()
    except NoResultFound:
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
                                            diseaseId=requested_disease.id,
                                            startDate=disease_info.startDate,
                                            endDate=None,
                                            treatment=disease_info.treatment)
        session.add(db_new_plant_disease)
        session.commit()
        return disease_info
    except ValidationError as error:
        raise HTTPException(status_code=400, detail=str(error))
    finally:
        if session.in_transaction():
            session.rollback()


@router.patch("/my-plants/{plant_id}/plant-disease")
async def update_disease_end_date(plant_id: int, update_info: EndDateDiseaseUpdate, user: AuthUser = Depends(get_current_user)):
    try:
        disease_log_to_update = (session.query(PlantDisease, Plant).join(Plant)
                                 .filter(PlantDisease.id == update_info.plant_disease_id, Plant.id == plant_id).one())
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Disease log not found")
    try:
        if disease_log_to_update[1].userId != user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        if disease_log_to_update[0].startDate.astimezone() > update_info.end_date.astimezone():
            raise HTTPException(status_code=400, detail='Disease cannot end before it started')
        log_update = {PlantDisease.endDate: update_info.end_date}
        session.execute(update(PlantDisease).where(PlantDisease.id == update_info.plant_disease_id).values(log_update))
        session.commit()
        return {"message": "disease end date updated"}
    finally:
        if session.in_transaction():
            session.rollback()

@router.get("/all-diseases")
async def all_diseases(user: AuthUser = Depends(get_current_user)):
    diseases = session.query(Disease).all()
    return diseases
