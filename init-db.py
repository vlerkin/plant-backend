from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Base, User

engine = create_engine("postgresql://test@localhost:5432/test", echo=True)
Base.metadata.create_all(engine)

with Session(engine) as session:
    zuzya = User(
        email="example@mail.com",
        password="passwordPASSWORD1",
        name="Zuzya",
    )
