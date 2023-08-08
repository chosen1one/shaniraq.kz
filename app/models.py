from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship, Session

from attrs import define

from .database import Base


#USERS
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    phone = Column(String, unique=True)
    password = Column(String)
    name = Column(String)
    city = Column(String)

    ad = relationship("Ad", back_populates="user")
    comment = relationship("Comment", back_populates="user")
    favorite = relationship("Favorite", back_populates="user")

@define
class UserCreate:
    username: str
    phone: str
    password: str
    name: str
    city: str

class UserRepository:
    def create(self, db: Session, user: UserCreate) -> User:
        db_user = User(
            username = user.username,
            phone = user.phone,
            password = user.password,
            name = user.name,
            city = user.city
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def update(self, db: Session, user_id: int, user: UserCreate) -> User:
        db_user = self.get_by_id(db, user_id)
        for key, value in user.dict().items():
            if value:
                setattr(db_user, key, value)
            
        db.commit()
        return db_user
    
    def get_by_id(self, db: Session, user_id: int) -> User:
        return db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, db: Session, username: str) -> User:
        return db.query(User).filter(User.username == username).first()
    

#ADS
class Ad(Base):
    __tablename__ = "ads"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True)
    price = Column(Integer)
    adress = Column(String)
    area = Column(Float)
    rooms_count = Column(Integer)
    description = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="ad")
    comment = relationship("Comment", back_populates="ad")
    favorite = relationship("Favorite", back_populates="ad")

@define
class AdCreate:
    type: str
    price: int
    adress: str
    area: float
    rooms_count: int
    description: str
    user_id: int

class AdRepository:
    def create(self, db: Session, ad: AdCreate) -> Ad:
        db_ad = Ad(
            type = ad.type,
            price = ad.price,
            adress = ad.adress,
            area = ad.area,
            rooms_count = ad.rooms_count,
            description = ad.description,
            user_id = ad.user_id
        )
        db.add(db_ad)
        db.commit()
        db.refresh(db_ad)
        return db_ad
    
    def update(self, db: Session, ad_id: int, ad: AdCreate) -> Ad:
        db_ad = self.get_by_id(db, ad_id)
        for key, value in ad.dict().items():
            if value:
                setattr(db_ad, key, value)
        db.commit()
        return db_ad
    
    def delete(self, db: Session, ad_id: int):
        db_ad = self.get_by_id(db, ad_id)
        if db_ad is None:
            return False
        db.delete(db_ad)
        db.commit()
        return True
    
    def get_filtered_result(self, db: Session, limit: int, offset: int, type: str, 
                            rooms_count: int, price_from: int, price_until: int) -> list[Ad]:
        res = db.query(Ad)
        if type:
            res = res.filter(Ad.type == type).all()
        if rooms_count:
            res = res.filter(Ad.rooms_count == rooms_count).all()
        if price_from:
            res = res.filter(Ad.price_from >= price_from).all()
        if price_until:
            res = res.filter(Ad.price_until <= price_until).all()
        
        
        return res

    def get_by_id(self, db: Session, ad_id: int) -> Ad:
        return db.query(Ad).filter(Ad.id == ad_id).first()


#COMMENTS
class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    author_id = Column(Integer, ForeignKey("users.id"))
    ad_id = Column(Integer, ForeignKey("ads.id"))

    user = relationship("User", back_populates="comment")
    ad = relationship("Ad", back_populates="comment")
 
@define
class CommentCreate:
    content: str
    ad_id: int
    author_id: int

class CommentRepository:
    def create(self, db: Session, comment: CommentCreate) -> Comment:
        db_comment = Comment(
            content=comment.content,
            ad_id = comment.ad_id,
            author_id = comment.author_id
        )
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
        return db_comment

    def update(self, db: Session, comment_id: int, comment: CommentCreate) -> Comment:
        db_comment = self.get_comments_by_id(db, comment_id)
        for key, value in comment.dict().items():
            if value:
                setattr(db_comment, key, value)
        db.commit()
        return db_comment
    
    def delete(self, db: Session, comment_id: int):
        db_comment = self.get_comments_by_id(db, comment_id)
        if db_comment is None:
            return False
        db.delete(db_comment)
        db.commit()
        return True
    
    def get_comments_by_id(self, db: Session, comment_id: int) -> Comment:
        return db.query(Comment).filter(Comment.id == comment_id).first()
    

#FAVORITES
class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ad_id = Column(Integer, ForeignKey("ads.id"))

    user = relationship("User", back_populates="favorite")
    ad = relationship("Ad", back_populates="favorite")

@define
class FavoriteCreate:
    user_id: int
    ad_id: int

class FavoriteRepository:
    def create(self, db: Session, favorite: FavoriteCreate) -> Favorite:
        db_favorite = Favorite(
            user_id = favorite.user_id,
            ad_id = favorite.ad_id
        )
        db.add(db_favorite)
        db.commit()
        db.refresh(db_favorite)
        return db_favorite

    def get_by_ids(self, db: Session, user_id: int, ad_id: int) -> Favorite:
        return db.query(Favorite).filter(Favorite.user_id == user_id, Favorite.ad_id == ad_id).first()
        
    def delete(self, db: Session, user_id: int, ad_id: int):
        db_favorite = self.get_by_ids(db, user_id, ad_id)
        if db_favorite is None:
            return False
        db.delete(db_favorite)
        db.commit()
        return True
    