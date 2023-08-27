from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    name: Mapped[str] = mapped_column(String(100))
    photo: Mapped[Optional[str]]

    accessTokens: Mapped[List["AccessToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class AccessToken(Base):
    __tablename__ = "access_token"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(36))
    nameToken: Mapped[str] = mapped_column(String(100))
    startDate: Mapped[datetime]
    endDate: Mapped[datetime]
    userId: Mapped[int] = mapped_column(ForeignKey("user_account.id"))

    user: Mapped["User"] = relationship(back_populates="accessTokens")


class Plant(Base):
    __tablename__ = "plant"

    id: Mapped[int] = mapped_column(primary_key=True)
    photo: Mapped[Optional[str]]
    name: Mapped[str] = mapped_column(String(100))
    howOftenWatering: Mapped[int]
    waterVolume: Mapped[float]
    light: Mapped[str]
    location: Mapped[Optional[str]]
    comment: Mapped[Optional[str]]
    species: Mapped[Optional[str]]

    waterLogs: Mapped[List["WaterLog"]] = relationship("plant", cascade="all, delete-orphan")
    fertilizerLogs: Mapped[List["FertilizerLog"]] = relationship("plant", cascade="all, delete-orphan")
    diseases: Mapped[List["PlantDisease"]] = relationship()

    @property
    def isHealthy(self):
        # todo: compute by PlantDisease data
        today = datetime.now()
        for disease in self.diseases:
            if disease.endDate is None or disease.endDate > today:
                return False
        return True


class WaterLog(Base):
    __tablename__ = "water_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    dateTime: Mapped[datetime]
    waterVolume: Mapped[float]
    plantId: Mapped[int] = mapped_column(ForeignKey("plant.id"))

    plant: Mapped["Plant"] = relationship(back_populates="waterLogs")


class FertilizerLog(Base):
    __tablename__ = "fertilizer_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str]
    quantity: Mapped[float]
    dateTime: Mapped[datetime]
    plantId: Mapped[int] = mapped_column(ForeignKey("plant.id"))

    plant: Mapped["Plant"] = relationship(back_populates="fertilizerLogs")


class Disease(Base):
    __tablename__ = "disease"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[Optional[str]]


class PlantDisease(Base):
    __tablename__ = "plant_disease"

    plantId: Mapped[int] = mapped_column(ForeignKey("plant.id"), primary_key=True)
    diseaseId: Mapped[int] = mapped_column(ForeignKey("disease.id"), primary_key=True)
    startDate: Mapped[Optional[datetime]]
    endDate: Mapped[Optional[datetime]]
    treatment: Mapped[Optional[str]]
    comment: Mapped[Optional[str]]
