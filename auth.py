import re
from datetime import datetime, timedelta

from fastapi import HTTPException, Depends, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.exc import NoResultFound

from config import Configuration, session
from interfaces import AuthUser
from models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

allow_guest_to_routes = [
    r"GET /me",
    r'GET /my-plants',
    r'GET /my-plants/\d+',
    r'POST /my-plants/\d+/watering',
]

allow_guest_to_routes_regex = r'^(' + '|'.join(allow_guest_to_routes) + ')$'


# password verification and hashing
def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_user(email: str):
    try:
        user_to_login = session.query(User).filter_by(email=email).one()
    except NoResultFound:
        return None

    return user_to_login


def authenticate_user(email: str, password: str):
    user = get_user(email)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=Configuration.token_expire_days)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Configuration.secret_key, algorithm=Configuration.algorithm)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), request: Request = None):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            Configuration.secret_key,
            algorithms=[Configuration.algorithm],
            options={'verify_aud': False}
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception

        guest: bool = payload.get("aud", "user") == "guest"
        if guest and not re.match(allow_guest_to_routes_regex, request.method + " " + request.url.path):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Guest account does not have the access"
            )

    except JWTError as error:
        print(error)
        raise credentials_exception
    user = get_user(email)
    if user is None:
        raise credentials_exception

    if guest:
        return AuthUser(id=user.id, name="Guest", email="", photo="", is_guest=True)
    else:
        return AuthUser(
            id=user.id,
            name=user.name,
            email=user.email,
            photo=user.photo_url,
            is_guest=False,
        )
