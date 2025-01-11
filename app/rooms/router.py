from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.users.auth import get_current_user
from sqlalchemy.sql import func
from sqlalchemy import and_, or_, not_
from app.rooms import schemas as room_schemas, models as room_models, crud
from app.bookings import models as booking_models  # Adjust path if needed
from app.users import schemas
from datetime import date
from loguru import logger

router = APIRouter()



# Set up logging
logger.add("app.log", rotation="500 MB", level="DEBUG")


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_room(
    room: schemas.RoomSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    logger.info(f"Room creation request received. User: {current_user.username}, Role: {current_user.role}")

    # Check for admin permissions
    if current_user.role != "admin":
        logger.warning(f"Permission denied for user {current_user.username}. Role: {current_user.role}")
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Preserve the original case for storage but use lowercase for validation
    original_room_number = room.room_number
    normalized_room_number = original_room_number.lower()
    logger.debug(f"Original room number: {original_room_number}, Normalized room number: {normalized_room_number}")

    # Check if a room with the normalized room_number already exists
    existing_room = (
        db.query(room_models.Room)
        .filter(func.lower(room_models.Room.room_number) == normalized_room_number)
        .first()
    )
    if existing_room:
        logger.warning(f"Room creation failed. Room {original_room_number} already exists in the database.")
        raise HTTPException(status_code=400, detail="Room with this number already exists")

    logger.info(f"Creating a new room: {original_room_number}")

    try:
        # Create the room using the original case
        new_room = crud.create_room(db, room)
        logger.info(f"Room {original_room_number} created successfully.")
        return {"message": "Room created successfully", "room": new_room}
    except Exception as e:
        logger.error(f"Error while creating room {original_room_number}: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while creating the room.")


@router.get("/", response_model=dict)
def list_rooms(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    Fetch a list of rooms with basic details: room number, room type, and amount.
    Also include the total number of rooms in the hotel.
    """
    # Fetch the list of rooms with pagination
    rooms = crud.get_rooms_with_pagination(skip=skip, limit=limit, db=db)
    
    # Convert SQLAlchemy rows to dictionaries
    serialized_rooms = crud.serialize_rooms(rooms)
    
    # Get the total count of rooms
    total_rooms = crud.get_total_room_count(db=db)
    
    # Return the response as a dictionary
    return {
        "total_rooms": total_rooms,  # Total number of rooms in the hotel
        "rooms": serialized_rooms,   # List of rooms
    }





@router.get("/available")
def list_available_rooms(db: Session = Depends(get_db)):
    today = date.today()

    # Query to get all rooms, no matter their availability status
    available_rooms_query = db.query(room_models.Room)

    # Exclude rooms with bookings that overlap with today
    available_rooms_query = available_rooms_query.filter(
        not_(
            room_models.Room.room_number.in_(
                db.query(booking_models.Booking.room_number)
                .filter(
                    booking_models.Booking.status.notin_(["checked-out", "cancelled"]),  # Exclude irrelevant bookings
                    # Check for overlapping bookings with today
                    and_(
                        booking_models.Booking.arrival_date <= today,  # Booking starts before or on today
                        booking_models.Booking.departure_date >= today,  # Booking ends after or on today
                    )
                )
            )
        )
    )

    # Fetch available rooms
    available_rooms = available_rooms_query.all()

    # Total rooms in the database
    total_rooms = db.query(room_models.Room).count()

    # If no rooms are available, return a fully booked message
    if not available_rooms:
        return {
            "message": "We are fully booked! No rooms are available for today.",
            "total_rooms": total_rooms,
            "total_available_rooms": 0,
            "available_rooms": [],
        }

    # Serialize the available rooms for the response
    serialized_rooms = [
        {
            "room_number": room.room_number,
            "room_type": room.room_type,
            "amount": room.amount,
        }
        for room in available_rooms
    ]

    return {
        "message": "Available rooms fetched successfully.",
        "total_rooms": total_rooms,
        "total_available_rooms": len(serialized_rooms),
        "available_rooms": serialized_rooms,
    }




@router.put("/{room_number}")
def update_room(
    room_number: str,
    room_update: room_schemas.RoomUpdateSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Normalize the room_number input to lowercase
    room_number = room_number.lower()

    # Fetch the room by the normalized room_number
    room = db.query(room_models.Room).filter(func.lower(room_models.Room.room_number) == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Prevent updates if the room is checked-in
    if room.status == "checked-in":
        raise HTTPException(
            status_code=400,
            detail="Room cannot be updated as it is currently checked-in"
        )

    # If a new room_number is provided, check for conflicts
    if room_update.room_number and room_update.room_number.lower() != room.room_number.lower():
        existing_room = db.query(room_models.Room).filter(
            func.lower(room_models.Room.room_number) == room_update.room_number.lower()
        ).first()
        if existing_room:
            raise HTTPException(status_code=400, detail="Room with this number already exists")
        room.room_number = room_update.room_number.lower()  # Update the room number to lowercase

    # Update other fields only if provided
    if room_update.room_type:
        room.room_type = room_update.room_type

    if room_update.amount is not None:
        room.amount = room_update.amount

    if room_update.status:
        if room_update.status not in ["available", "booked", "maintenance", "reserved"]:
            raise HTTPException(status_code=400, detail="Invalid status value")
        room.status = room_update.status

    # Commit the changes to the database
    db.commit()
    db.refresh(room)

    return {"message": "Room updated successfully", "room": room}



@router.get("/summary")
def room_summary(
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Generate a summary of all rooms, including counts of:
    - Checked-in rooms
    - Reserved rooms (both today and future, counted separately)
    - Available rooms for today
    """
    today = date.today()

    try:
        # Total number of rooms
        total_rooms = db.query(room_models.Room).count()

        # Checked-in rooms today
        total_checked_in_rooms = (
            db.query(booking_models.Booking)
            .filter(
                booking_models.Booking.status == "checked-in",
                booking_models.Booking.arrival_date <= today,
                booking_models.Booking.departure_date >= today,
            )
            .count()
        )

        # Reserved rooms (count reservations separately)
        total_reserved_rooms = (
            db.query(booking_models.Booking)
            .filter(
                booking_models.Booking.status == "reserved",
                booking_models.Booking.arrival_date >= today,
            )
            .count()
        )

        # Occupied rooms today (checked-in + reserved for today)
        occupied_rooms_today = (
            db.query(booking_models.Booking.room_number)
            .filter(
                or_(
                    booking_models.Booking.status == "checked-in",
                    and_(
                        booking_models.Booking.status == "reserved",
                        booking_models.Booking.arrival_date <= today,
                        booking_models.Booking.departure_date >= today,
                    ),
                )
            )
            .distinct()
            .all()
        )
        occupied_room_numbers_today = {room.room_number for room in occupied_rooms_today}

        # Total available rooms
        total_available_rooms = total_rooms - len(occupied_room_numbers_today)

        # Determine the appropriate message
        message = (
            f"{total_available_rooms} room(s) available."
            if total_available_rooms > 0
            else "Fully booked! All rooms are occupied for today."
        )

        return {
            "total_rooms": total_rooms,
            "rooms_checked_in": total_checked_in_rooms,
            "rooms_reserved": total_reserved_rooms,
            "rooms_available": total_available_rooms,
            "message": message,
        }

    except Exception as e:
        logger.error(f"Error generating room summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching room summary: {str(e)}",
        )



@router.delete("/{room_number}")
def delete_room(
    room_number: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    # Ensure only admin can delete rooms
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Normalize the room_number input to lowercase
    room_number = room_number.lower()

    # Fetch the room by the normalized room_number
    room = db.query(room_models.Room).filter(func.lower(room_models.Room.room_number) == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Check if the room is tied to any bookings
    bookings = db.query(booking_models.Booking).filter(
        func.lower(booking_models.Booking.room_number) == room_number
    ).all()
    if bookings:
        raise HTTPException(
            status_code=400,
            detail=f"Room {room_number} cannot be deleted as it is tied to one or more bookings."
        )

    # Delete the room if it is available
    try:
        db.delete(room)
        db.commit()
        return {"message": f"Room {room_number} deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while deleting the room: {str(e)}"
        )