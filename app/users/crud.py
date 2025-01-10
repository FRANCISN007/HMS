from sqlalchemy.orm import Session
from app.users import models, schemas
from app.rooms import models, schemas
# Correct imports
from app.users.models import User  # Correct import for User model
from app.users import schemas as use_schema
#from app.rooms.models import Room
#from users.models import User



def create_user(db: Session, user: use_schema.UserSchema, hashed_password: str):
    # Create the new user using the correct User model
    new_user = User(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role  # Set the role here
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()



def get_all_users(db: Session, skip: int = 0, limit: int = 10):
    # Fetch all user fields (ORM objects) from the database
    return db.query(User).offset(skip).limit(limit).all()

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
    user = db.query(User).filter(User.username == username).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False