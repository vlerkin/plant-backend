from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from config import Configuration
from models import Base, User, Plant

engine = create_engine(Configuration.connection_string, echo=True)
Base.metadata.create_all(engine)

with Session(engine) as session:
    zuzya = User(
        email="example@mail.com",
        password="passwordPASSWORD1",
        name="Zuzya",
        plants=[
            Plant(
                name="Ficus Leonid",
                howOftenWatering=7,
                waterVolume=0.5,
                light="full sun",
            ),
            Plant(
                name="Aloe Oleg",
                howOftenWatering=7,
                waterVolume=0.5,
                light="full sun",
            )
        ]
    )
    session.add(zuzya)
    session.commit()
