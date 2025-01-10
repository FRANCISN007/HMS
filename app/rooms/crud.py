from sqlalchemy.orm import Session
from app.rooms import models, schemas
from app.rooms import models as room_models


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




def get_rooms_with_pagination(skip: int, limit: int, db: Session):
    """
    Fetch a list of rooms with basic details using pagination.
    """
    return db.query(room_models.Room.room_number, room_models.Room.room_type, room_models.Room.amount) \
        .offset(skip) \
        .limit(limit) \
        .all()

def serialize_rooms(rooms):
    """
    Convert SQLAlchemy rows to dictionaries.
    """
    return [
        {
            "room_number": room.room_number,
            "room_type": room.room_type,
            "amount": room.amount,
        }
        for room in rooms
    ]

def get_total_room_count(db: Session):
    """
    Fetch the total number of rooms in the hotel.
    """
    return db.query(room_models.Room).count()