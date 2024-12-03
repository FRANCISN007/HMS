from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.users.auth import get_current_user
from app.database import get_db
from app.reservations import schemas, models  # Import reservation-specific schemas and models
from app.rooms import schemas, models
from app.reservations import schemas as reservation_schemas, models as reservation_models
from app.rooms import schemas as room_schemas, models as room_models
from sqlalchemy import and_
from app.reservations.crud import check_overlapping_check_in, check_overlapping_reservations
from app.users import schemas


router = APIRouter()




from datetime import date

@router.post("/")
def create_reservation(
    reservation: reservation_schemas.ReservationSchema,
    db: Session = Depends(get_db),
):
    # Validate mandatory fields
    if not reservation.room_number:
        raise HTTPException(status_code=400, detail="Room number is required.")
    
    if reservation.arrival_date > reservation.departure_date:
        raise HTTPException(
            status_code=400, 
            detail="Arrival date must be before or on the same day as the departure date."
        )
    
    # Ensure the reservation is for a future date
    if reservation.arrival_date <= date.today():
        raise HTTPException(
            status_code=400,
            detail="Reservations cannot be made for today or past dates. Use the check-in functionality instead."
        )
    
    # Validate if the room exists
    room = db.query(room_models.Room).filter(room_models.Room.room_number == reservation.room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")
    
    # Check if the room is already checked in
    checked_in_reservation = check_overlapping_check_in(
        db=db,
        room_number=reservation.room_number,
        arrival_date=reservation.arrival_date,
        departure_date=reservation.departure_date
    )
    if checked_in_reservation:
        raise HTTPException(
            status_code=400,
            detail=f"Room {reservation.room_number} is already checked in by another guest "
                   f"from {checked_in_reservation.arrival_date} to {checked_in_reservation.departure_date}."
        )
    
    # Check for overlapping reservations or active check-ins for the same room
    overlapping_reservation = check_overlapping_reservations(
        db=db,
        room_number=reservation.room_number,
        arrival_date=reservation.arrival_date,
        departure_date=reservation.departure_date
    )
    if overlapping_reservation:
        raise HTTPException(
            status_code=400,
            detail=f"Room {reservation.room_number} is already occupied or reserved from "
                   f"{overlapping_reservation.arrival_date} to {overlapping_reservation.departure_date}.",
        )

    # Check if the room is under maintenance
    if room.status == "maintenance":
        raise HTTPException(
            status_code=400,
            detail=f"Room {reservation.room_number} is under maintenance and cannot be reserved.",
        )
    
    try:
        # Create a new reservation
        new_reservation = reservation_models.Reservation(
            room_number=reservation.room_number,
            guest_name=reservation.guest_name,
            arrival_date=reservation.arrival_date,
            departure_date=reservation.departure_date,
            status="reserved",
        )
        db.add(new_reservation)
        db.commit()
        db.refresh(new_reservation)
        
        # Update room status to "reserved"
        room.status = "reserved"
        db.commit()

        return {"message": "Reservation created successfully.", "reservation": new_reservation}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.get("/reserved", response_model=reservation_schemas.ReservedRoomsListSchema)
def list_reserved_rooms(db: Session = Depends(get_db), 
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    try:
        # Querying the reserved rooms
        reserved_rooms = (
            db.query(
                room_models.Room.room_number,
                room_models.Room.room_type,
                reservation_models.Reservation.guest_name,
                reservation_models.Reservation.arrival_date,
                reservation_models.Reservation.departure_date,
            )
            .join(
                reservation_models.Reservation,
                room_models.Room.room_number == reservation_models.Reservation.room_number
            )
            .filter(room_models.Room.status == "reserved")
            .all()
        )

        # Structuring the response
        return {
            "total_reserved_rooms": len(reserved_rooms),
            "reserved_rooms": [
                {
                    "room_number": room.room_number,
                    "room_type": room.room_type,
                    "guest_name": room.guest_name,
                    "arrival_date": room.arrival_date,
                    "departure_date": room.departure_date,
                }
                for room in reserved_rooms
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.delete("/delete-reservation/")
def delete_reservation(
    room_number: str,
    guest_name: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Deletes a reservation for a specific guest and room number.
    Only admins or the guest who made the reservation can delete it.
    """
    try:
        # Fetch the reservation by room number and guest name
        reservation = db.query(reservation_models.Reservation).filter(
            reservation_models.Reservation.room_number == room_number,
            reservation_models.Reservation.guest_name == guest_name,
        ).first()

        if not reservation:
            raise HTTPException(
                status_code=404,
                detail=f"No reservation found for room {room_number} and guest {guest_name}."
            )

        # Admins can delete any reservation; regular users can delete their own
        if current_user.role != "admin" and reservation.guest_name != current_user.username:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to delete this reservation.",
            )

        # Delete the reservation
        db.delete(reservation)
        db.commit()

        # Check if other reservations exist for the same room
        remaining_reservations = db.query(reservation_models.Reservation).filter(
            reservation_models.Reservation.room_number == room_number
        ).count()

        if remaining_reservations == 0:
            # If no other reservations exist, update the room status
            room = db.query(room_models.Room).filter(
                room_models.Room.room_number == room_number
            ).first()

            if room:
                room.status = "available"
                db.commit()

        return {
            "message": f"Reservation for room {room_number} and guest {guest_name} successfully deleted.",
            "room_status": "available" if remaining_reservations == 0 else "reserved",
        }

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while deleting the reservation: {str(e)}",
        )
