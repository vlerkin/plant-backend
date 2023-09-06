from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from config import Configuration


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    name: Mapped[str] = mapped_column(String(100))
    photo: Mapped[Optional[str]]

    plants: Mapped[List["Plant"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    accessTokens: Mapped[List["AccessToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class AccessToken(Base):
    __tablename__ = "access_token"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(36))
    nameToken: Mapped[str] = mapped_column("name_token", String(100))
    startDate: Mapped[datetime] = mapped_column("start_date")
    endDate: Mapped[datetime] = mapped_column("end_date")
    userId: Mapped[int] = mapped_column("user_id", ForeignKey("user_account.id"))

    user: Mapped["User"] = relationship(back_populates="accessTokens")


class Plant(Base):
    __tablename__ = "plant"

    id: Mapped[int] = mapped_column(primary_key=True)
    photo: Mapped[Optional[str]]
    name: Mapped[str] = mapped_column(String(100))
    howOftenWatering: Mapped[int] = mapped_column("how_often_watering")
    waterVolume: Mapped[float] = mapped_column("water_volume")
    light: Mapped[str]
    location: Mapped[str]
    comment: Mapped[Optional[str]]
    species: Mapped[Optional[str]]
    userId: Mapped[int] = mapped_column("user_id", ForeignKey("user_account.id"))

    user: Mapped["User"] = relationship(back_populates="plants")
    waterLogs: Mapped[List["WaterLog"]] = relationship(cascade="all, delete-orphan", back_populates="plant")
    fertilizerLogs: Mapped[List["FertilizerLog"]] = relationship(cascade="all, delete-orphan", back_populates="plant")
    diseases: Mapped[List["PlantDisease"]] = relationship()

    @property
    def photo_url(self):
        return Configuration.image_hostname + self.photo if self.photo else None

    @property
    def is_healthy(self):
        # todo: compute by PlantDisease data
        yesterday = datetime.now() - timedelta(days=1)
        for disease in self.diseases:
            if disease.endDate is None or disease.endDate >= yesterday:
                return False
        return True

    @property
    def time_to_water(self):
        today = datetime.now()
        watering = None
        for record in self.waterLogs:
            if not watering or watering.dateTime < record.dateTime:
                watering = record

        if not watering:
            return True

        difference_in_days = (today - watering.dateTime).days
        if difference_in_days >= self.howOftenWatering:
            return True
        return False


class WaterLog(Base):
    __tablename__ = "water_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    dateTime: Mapped[datetime] = mapped_column("date_time")
    waterVolume: Mapped[float] = mapped_column("water_volume")
    plantId: Mapped[int] = mapped_column("plant_id", ForeignKey("plant.id"))

    plant: Mapped["Plant"] = relationship(back_populates="waterLogs")


class FertilizerLog(Base):
    __tablename__ = "fertilizer_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str]
    quantity: Mapped[float]
    dateTime: Mapped[datetime] = mapped_column("date_time")
    plantId: Mapped[int] = mapped_column("plant_id", ForeignKey("plant.id"))

    plant: Mapped["Plant"] = relationship(back_populates="fertilizerLogs")


class Disease(Base):
    __tablename__ = "disease"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str]


class PlantDisease(Base):
    __tablename__ = "plant_disease"

    id: Mapped[int] = mapped_column(primary_key=True)
    plantId: Mapped[int] = mapped_column("plant_id", ForeignKey("plant.id"))
    diseaseId: Mapped[int] = mapped_column("disease_id", ForeignKey("disease.id"))
    startDate: Mapped[datetime] = mapped_column("start_date")
    endDate: Mapped[Optional[datetime]] = mapped_column("end_date")
    treatment: Mapped[Optional[str]]

    disease: Mapped["Disease"] = relationship()

    @property
    def disease_type(self):
        return self.disease.type
