from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, EmailStr, FutureDatetime


class NewUser(BaseModel):
    name: str = Field(..., max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=10)


class ErrorMessage(BaseModel):
    message: str


class LightEnum(str, Enum):
    full_sun = "full sun"
    part_shadow = "partial shadow"
    full_shadow = "full shadow"


class LocationEnum(str, Enum):
    south = "south"
    north = "north"
    east = "east"
    west = "west"
    south_east = "south_east"
    south_west = "south_west"
    north_east = "north_east"
    north_west = "north_west"


class PlantUpdate(BaseModel):
    name: str = Field(..., max_length=100)
    howOftenWatering: int = Field(..., gt=0)
    waterVolume: float = Field(..., gt=0)
    light: LightEnum
    location: LocationEnum
    photo: str | None
    comment: str | None
    species: str | None


class LoginUser(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=10)


class UserProfile(BaseModel):
    name: str
    email: str
    photo: str | None


class MyPlants(BaseModel):
    id: int
    name: str
    howOftenWatering: int
    location: str
    species: str | None
    waterVolume: float
    light: str
    comment: str | None
    userId: int
    is_healthy: bool | None
    time_to_water: bool | None
    photo_url: str | None


class UserUpdate(BaseModel):
    email: EmailStr
    password: str | None
    name: str = Field(..., max_length=100)
    photo: str | None


class CreateFertilizing(BaseModel):
    type: str = Field(..., max_length=300)
    quantity: float


class PlantDiseaseCreate(BaseModel):
    diseaseId: int
    startDate: datetime
    endDate: datetime
    treatment: str | None


class PlantInfo(BaseModel):
    id: int
    name: str
    howOftenWatering: int
    location: str
    species: str | None
    waterVolume: float
    light: str
    comment: str | None
    userId: int
    photo_url: str | None


class WateringLog(BaseModel):
    id: int
    plantId: int
    dateTime: datetime
    waterVolume: float


class FertilizingLog(BaseModel):
    id: int
    plantId: int
    dateTime: datetime
    type: str
    quantity: int


class DiseaseLog(BaseModel):
    id: int
    plantId: int
    startDate: datetime
    endDate: datetime | None
    treatment: str | None
    disease_type: str


class PlantIndividualInfo(BaseModel):
    info: PlantInfo
    watering_log: WateringLog | None
    fertilizing_log: FertilizingLog | None
    disease_log: list[DiseaseLog] | None


class GuestInput(BaseModel):
    guest_name: str = Field(..., min_length=3)
    end_date: FutureDatetime


class TokenDelete(BaseModel):
    token_id: int

