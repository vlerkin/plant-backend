from sqlalchemy.exc import NoResultFound

from config import session
from models import Plant


def get_user_plant_by_id(user_id: int, plant_id: int) -> Plant | None:
    try:
        return session.query(Plant).filter_by(userId=user_id, id=plant_id).one()
    except NoResultFound:
        return None
