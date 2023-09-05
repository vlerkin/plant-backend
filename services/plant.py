from sqlalchemy import desc
from sqlalchemy.exc import NoResultFound

from config import session
from models import Plant, WaterLog, FertilizerLog, PlantDisease


def get_user_plant_by_id(user_id: int, plant_id: int) -> Plant | None:
    try:
        return session.query(Plant).filter_by(userId=user_id, id=plant_id).one()
    except NoResultFound:
        return None


def get_last_plant_watering(plant_id: int) -> WaterLog | None:
    try:
        return session.query(
            WaterLog).where(WaterLog.plantId == plant_id).order_by(desc(WaterLog.dateTime)).limit(1).one()
    except NoResultFound:
        return None


def get_last_plant_fertilizing(plant_id: int):
    try:
        return session.query(
            FertilizerLog).where(FertilizerLog.plantId == plant_id).order_by(desc(FertilizerLog.dateTime)).limit(
            1).one()
    except NoResultFound:
        return None


def get_plant_diseases(plant_id: int, limit: int = 10) -> list[PlantDisease]:
    return session.query(
        PlantDisease).where(PlantDisease.plantId == plant_id).order_by(desc(PlantDisease.startDate)).limit(limit).all()
