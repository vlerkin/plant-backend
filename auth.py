from datetime import datetime, timedelta

from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import Configuration
from models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# password verification and hashing
def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_user(session: Session, email: str):
    user_to_login = session.query(User).filter_by(email=email).one()
    if not user_to_login:
        return False
    return user_to_login


def authenticate_user(session: Session, email: str, password: str):
    user = get_user(session, email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=Configuration.tokenExpireDays)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Configuration.secretKey, algorithm=Configuration.algorithm)
    return encoded_jwt




