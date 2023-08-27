from sqlalchemy import create_engine
from models import Base

engine = create_engine("postgresql://test@localhost:5432/test", echo=True)
Base.metadata.create_all(engine)


