import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from marshmallow import ValidationError
from sqlalchemy import update
from sqlalchemy.exc import NoResultFound

from auth import get_password_hash, authenticate_user, create_access_token, get_current_user
from interfaces import NewUser, LoginUser, UserProfile, UserUpdate, GuestInput, TokenDelete, AuthUser
from models import User, AccessToken
from config import session

router = APIRouter()


# register a new user
@router.post("/register")
async def create_new_user(new_user: NewUser):
    password = get_password_hash(new_user.password)
    try:
        db_new_user = User(
            name=new_user.name,
            password=password,
            email=new_user.email,
        )
        session.add(db_new_user)
        session.commit()
        session.refresh(db_new_user)
        return new_user
    except ValidationError as error:
        raise HTTPException(status_code=400, detail=str(error))


# log in a user
@router.post("/login")
async def login_user(user_to_login: LoginUser):
    user = authenticate_user(user_to_login.email, user_to_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email}
    )
    return {"access_token": access_token, "token_type": "bearer"}


# get user profile
@router.get("/me", response_model=UserProfile)
async def show_me(user: AuthUser = Depends(get_current_user)):
    return user


@router.patch("/me")
async def edit_profile(user_info: UserUpdate, user: AuthUser = Depends(get_current_user)):
    user_id = user.id
    user_to_update = session.query(User).filter_by(id=user_id).one()
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")

    photo = user.photo
    name = user.name
    email = user.email
    if user_info.photo:
        photo = user_info.photo
    if user_info.email:
        email = user_info.email
    if user_info.name:
        name = user_info.name

    # if user provided new password, check it and hash before updating
    if user_info.password and get_password_hash(user_info.password) != user_to_update.password:
        hashed_password = get_password_hash(user_info.password)
        user_update = {User.name: name,
                       User.email: email,
                       User.photo: photo,
                       User.password: hashed_password
                       }
        session.execute(update(User).where(User.id == user_id).values(user_update))
        session.commit()
        return {"message": "user updated"}
    # if user did not provide a new password update user with the existing one
    else:
        user_update = {User.name: user_info.name,
                       User.email: user_info.email,
                       User.photo: photo,
                       User.password: user_to_update.password}
        session.execute(update(User).where(User.id == user_id).values(user_update))
        session.commit()
        return {"message": "user updated"}


# access token endpoints
@router.get("/access-tokens")
async def get_all_tokens(user: AuthUser = Depends(get_current_user)):
    access_tokens_of_user = session.query(AccessToken).filter(AccessToken.userId == user.id).all()
    return access_tokens_of_user


@router.post("/access-tokens")
async def create_guest_token(guest_input: GuestInput, user: AuthUser = Depends(get_current_user)):
    access_token = AccessToken(
        token=str(uuid.uuid4()),
        nameToken=guest_input.guest_name,
        startDate=datetime.now(),
        endDate=guest_input.end_date,
        userId=user.id,
    )
    session.add(access_token)
    session.commit()

    session.refresh(access_token)
    return access_token


@router.delete("/access-tokens")
async def delete_guest_token(token: TokenDelete, user: AuthUser = Depends(get_current_user)):
    try:
        token_to_delete = session.query(
            AccessToken).filter(AccessToken.id == token.token_id, AccessToken.userId == user.id).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Token not found")

    session.delete(token_to_delete)
    session.commit()
    return {"message": "Token deleted"}


@router.get("/access-tokens/authorize/{access_token}")
async def authorize_guest(access_token: str):
    try:
        access_token = session.query(AccessToken).filter_by(token=access_token).one()
    except NoResultFound:
        raise HTTPException(status_code=401, detail="Authorization failed")

    if access_token.endDate < datetime.now():
        raise HTTPException(status_code=403, detail="Access denied")

    token = create_access_token(
        data={"sub": access_token.user.email, "aud": "guest"},
        expires_delta=(access_token.endDate - datetime.now())
    )
    return {"guest_token": token, "token_type": "bearer"}