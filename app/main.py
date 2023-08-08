from fastapi import FastAPI, Depends, HTTPException, Response, Form, Cookie, Request
from fastapi.security import OAuth2PasswordBearer

import json
from jose import jwt

from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from .database import SessionLocal, Base, engine
from .models import User, UserRepository, UserCreate
from .models import Ad, AdRepository, AdCreate
from .models import Comment, CommentRepository, CommentCreate
from .models import Favorite, FavoriteRepository, FavoriteCreate

Base.metadata.create_all(bind=engine)

app = FastAPI()
users_repository = UserRepository()
ads_repository = AdRepository()
comments_repository = CommentRepository()
favorites_repository = FavoriteRepository()

oauth2 = OAuth2PasswordBearer(tokenUrl="auth/users/login")


def encode_jwt(user_id: int) -> str:
    payload = { "user_id": user_id }
    token = jwt.encode(payload, "chosenone")
    return token

def decode_jwt(token: str) -> int:
    try:
        payload = jwt.decode(token, "chosenone")
        return payload["user_id"]
    except:
        HTTPException(status_code=401, details="Unauthorized")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class UserCreateRequest(BaseModel):
    username: str = None
    phone: str = None
    password: str = None
    name: str = None
    city: str = None

class UserReadResponse(BaseModel):
    id: int
    username: str
    phone: str
    name: str
    city: str

class AdCreateRequest(BaseModel):
    type: str = None
    price: int = None
    adress: str = None
    area: float = None
    rooms_count: int = None
    description: str = None

class AdReadResponse(BaseModel):
    id: int
    type: str
    price: int
    adress: str
    area: float
    rooms_count: int
    description: str
    user_id: int
    total_comments: int

class FilteredAdReadResponse(BaseModel):
    id: int
    type: str
    price: int
    adress: str
    area: float
    rooms_count: int

class CommentCreateRequest(BaseModel):
    content: str = None
    ad_id: int = None
    author_id: int = None

class CommentReadResponse(BaseModel):
    id: int
    content: str
    author_id: int

class FavoriteReadResponse(BaseModel):
    id: int
    adress: str


@app.post("/auth/users")
def post_users(user: UserCreateRequest, db: Session = Depends(get_db)):
    users_repository.create(db, UserCreate(
        username = user.username,
        phone = user.phone,
        password = user.password,
        name = user.name,
        city = user.city
    ))
    return Response(status_code=200)

@app.post("/auth/users/login")
def post_login(username: str = Form(), password: str = Form(), db: Session = Depends(get_db)):
    user = users_repository.get_by_username(db, username)
    if not user or user.password != password:
        return HTTPException(status_code=404, detail="Wrong username or password!")
    token = encode_jwt(user.id)
    return {"access_token": token, "type": "bearer"}

@app.patch("/auth/users/me")
def patch_users(user: UserCreateRequest, token: str = Depends(oauth2), db: Session = Depends(get_db)):
    user_id = decode_jwt(token)
    db_user = users_repository.update(db, user_id, user)
    return Response(status_code=200)

@app.get("/auth/users/me", response_model=UserReadResponse)
def get_profile(token: str = Depends(oauth2), db : Session = Depends(get_db)):
    user_id = decode_jwt(token)
    user = users_repository.get_by_id(db, user_id)
    return user


@app.post("/shanyraks")
def post_ads(ad: AdCreateRequest, token: str = Depends(oauth2), db: Session = Depends(get_db)):
    owner_id = decode_jwt(token)
    db_ad = ads_repository.create(db, AdCreate(
            type = ad.type,
            price = ad.price,
            adress = ad.adress,
            area = ad.area,
            rooms_count = ad.rooms_count,
            description = ad.description,
            user_id = owner_id   
    ))

    return { "id": db_ad.id }

@app.get("/shanyraks/{id}", response_model=AdReadResponse)
def get_ads(id: int, db: Session = Depends(get_db)):
    ad = ads_repository.get_by_id(db, id)
    if ad is None:
        raise HTTPException(status_code=404, detail="Ad not found")
    ad.total_comments = len(ad.comment)
    return ad

@app.patch("/shanyraks/{id}")
def patch_ads(id: int, ad: AdCreateRequest, token: str = Depends(oauth2), db: Session = Depends(get_db)):
    db_ad = ads_repository.update(db, id, ad)
    if db_ad is None:
        raise HTTPException(status_code=404, detail="Ad not found")
    user_id = decode_jwt(token)
    if user_id != db_ad.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return Response(status_code=200)

@app.delete("/shanyraks/{id}")
def delete_ads(id: int, token: str = Depends(oauth2), db: Session = Depends(get_db)):
    db_ad = ads_repository.get_by_id(db, id)
    if db_ad is None:
        raise HTTPException(status_code=404, detail="Ad not found")
    user_id = decode_jwt(token)
    if user_id != db_ad.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    ads_repository.delete(db, id)
    return Response(status_code=200)


@app.post("/shanyraks/{id}/comments")
def post_comments(id: int, comment: CommentCreateRequest, token: str = Depends(oauth2), db: Session = Depends(get_db)):
    ad = ads_repository.get_by_id(db, id)
    if ad is None:
        raise HTTPException(status_code=404, detail="Ad not found")
    user_id = decode_jwt(token)
    db_comment = comments_repository.create(db, CommentCreate(
        content = comment.content,
        ad_id = ad.id,
        author_id = user_id
    ))
    return Response(status_code=200)
  
@app.get("/shanyraks/{id}/comments", response_model=List[CommentReadResponse])
def get_comments(id: int, db: Session = Depends(get_db)):
    ad = ads_repository.get_by_id(db, id)
    if ad is None:
        raise HTTPException(status_code=404, detail="Ad not found")
    return ad.comment

@app.patch("/shanyraks/{id}/comments/{comment_id}")
def patch_comments(id: int, comment_id: int, comment: CommentCreateRequest, token: str = Depends(oauth2), db: Session = Depends(get_db)):
    db_comment = comments_repository.update(db, comment_id, comment)
    if db_comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    user_id = decode_jwt(token)
    if user_id != db_comment.author_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return Response(status_code=200)

@app.delete("/shanyraks/{id}/comments/{comment_id}")
def delete_comments(id: int, comment_id: int, token: str = Depends(oauth2), db: Session = Depends(get_db)):
    db_comment = comments_repository.get_comments_by_id(db, comment_id)
    if db_comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    user_id = decode_jwt(token)
    if user_id != db_comment.author_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    comments_repository.delete(db, comment_id)
    return Response(status_code=200)


@app.post("/auth/users/favorites/shanyraks/{id}")
def post_favorite(id: int, token: str = Depends(oauth2), db: Session = Depends(get_db)):
    ad = ads_repository.get_by_id(db, id)
    if ad is None:
        raise HTTPException(status_code=404, detail="Ad not found")
    us_id = decode_jwt(token)
    if favorites_repository.get_by_ids(db, us_id, ad.id) is None:
        db_favorite = favorites_repository.create(db, FavoriteCreate(
            user_id = us_id,
            ad_id = ad.id
        ))

    return Response(status_code=200)

@app.get("/auth/users/favorites/shanyraks")
def get_favorites(token: str = Depends(oauth2), db: Session = Depends(get_db)):
    user_id = decode_jwt(token)
    user = users_repository.get_by_id(db, user_id)
    favorites = user.favorite
    response = []
    for favorite in favorites:
        db_ad_adress = ads_repository.get_by_id(db, favorite.ad_id).adress
        response.append(FavoriteReadResponse(id = favorite.ad_id, adress = db_ad_adress))
    
    return {"shanyraks": response}

@app.delete("/auth/users/favorites/shanyraks/{id}")
def delete_favorites(id: int, token: str = Depends(oauth2), db: Session = Depends(get_db)):
    ad = ads_repository.get_by_id(db, id)
    if ad is None:
        raise HTTPException(status_code=404, detail="Ad not found")
    user_id = decode_jwt(token)
    if user_id != ad.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    favorites_repository.delete(db, user_id, ad.id)
    return Response(status_code=200)


@app.get("/shanyraks")
def get_ads(limit: int, offset: int,
            type: str | None = None, rooms_count: int | None = None,
            price_from: int | None = None, price_until: int | None = None,
            db: Session = Depends(get_db)):
    
    res = db.query(Ad)
    print(res)
    if type:
        res = res.filter(Ad.type == type).all()
    if rooms_count:
        res = res.filter(Ad.rooms_count == rooms_count).all()
    if price_from:
        res = res.filter(Ad.price_from >= price_from).all()
    if price_until:
        res = res.filter(Ad.price_until <= price_until).all()

    return {
        "objects": res
    }