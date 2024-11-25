from sqlalchemy.orm import Session
import models, schemas

def create_user(db: Session, user: schemas.UserSchema, hashed_password: str):
    new_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role  # Set the role here
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_all_users(db: Session, skip: int = 0, limit: int = 10):
    # Fetch all user fields (ORM objects) from the database
    return db.query(models.User).offset(skip).limit(limit).all()

def create_room(db: Session, room: schemas.RoomSchema):
    db_room = models.Room(
        room_number=room.room_number,
        room_type=room.room_type,
        amount=room.amount,
        status=room.status
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def delete_user_by_username(db: Session, username: str):
    user = db.query(models.User).filter(models.User.username == username).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False
