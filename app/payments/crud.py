from fastapi import  HTTPException
from sqlalchemy.orm import Session
from app.payments import models as payment_models, schemas as payment_schemas
from app.bookings import models as booking_models
from datetime import datetime
from typing import Optional
from app.rooms import models 
from loguru import logger
from sqlalchemy import between


# Set up logging
logger.add("app.log", rotation="500 MB", level="DEBUG")


def create_payment(
    db: Session,
    payment: payment_schemas.PaymentCreateSchema,
    booking_id: int,
    balance_due: float,
    status: str
):
    """
    Create a new payment for a booking and associate it with the booking.
    """
    # Step 1: Ensure the booking exists
    booking = db.query(booking_models.Booking).filter(booking_models.Booking.id == booking_id).first()
    if not booking:
        raise Exception(f"Booking with ID {booking_id} does not exist.")

    # Step 2: Create the new payment record
    new_payment = payment_models.Payment(
        booking_id=booking_id,  # Correctly assign the booking_id here
        room_number=booking.room_number,  # Extract room number from the booking record
        guest_name=booking.guest_name,  # Extract guest name from the booking record
        booking_cost=payment.booking_cost,
        amount_paid=payment.amount_paid,
        balance_due=balance_due,
        discount_allowed=payment.discount_allowed,
        payment_method=payment.payment_method,
        payment_date=payment.payment_date.isoformat(),
        status=status
    )

    # Step 3: Add and commit the payment to the database
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    return new_payment


def get_room_by_number(db: Session, room_number: str):
    # This function will check if the room exists in the database
    return db.query(models.Room).filter(models.Room.room_number == room_number).first()


def get_payment_by_guest_and_room(db: Session, guest_name: str, room_number: str):
    return db.query(payment_models.Payment).filter(
        payment_models.Payment.guest_name == guest_name,
        payment_models.Payment.room_number == room_number
    ).first()


def get_payment_by_booking_id(db: Session, booking_id: int):
    """
    Get payment details for a specific booking ID.
    """
    try:
        payment = db.query(payment_models.Payment).filter(
            payment_models.Payment.booking_id == booking_id
        ).first()
        return payment
    except Exception as e:
        raise Exception(f"Error retrieving payment for booking ID {booking_id}: {str(e)}")




# Assuming you're using SQLAlchemy

# Assuming you're using SQLAlchemy

def get_list_payments_no_pagination(
    db: Session, start_date: Optional[datetime], end_date: Optional[datetime]
):
    query = db.query(payment_models.Payment)  # Assuming `Payment` is the model representing the payments

    # Apply date filters if provided
    if start_date:
        query = query.filter(payment_models.Payment.payment_date >= start_date)
    if end_date:
        query = query.filter(payment_models.Payment.payment_date <= end_date)

    # Order the query results by payment_date in descending order
    query = query.order_by(payment_models.Payment.payment_date.desc())

    # Fetch all the results without pagination
    payments = query.all()

    return payments



def get_payment_by_id(db: Session, payment_id: int):
    """
    Retrieve a payment by its ID.
    """
    try:
        logger.info(f"Querying payment with ID: {payment_id}")
        
        # Perform the query
        payment = db.query(payment_models.Payment).filter(payment_models.Payment.id == payment_id).first()
        
        # Check if the payment exists
        if not payment:
            logger.warning(f"No payment found with ID: {payment_id}")
        
        return payment

    except Exception as e:
        logger.error(f"Error retrieving payment by ID {payment_id}: {str(e)}")
        # Optionally log the stack trace for more context
        logger.exception(e)
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while retrieving the payment with ID {payment_id}."
        )

  
  
def update_payment_with_new_amount(
    db: Session, payment_id: int, amount_paid: float, discount_allowed: Optional[float], balance_due: float, status: str
):
    """
    Update an existing payment with new amount paid and discount applied.
    """
    payment = db.query(payment_models.Payment).filter(payment_models.Payment.id == payment_id).first()
    if payment:
        payment.amount_paid += amount_paid
        payment.discount_allowed = discount_allowed
        payment.balance_due = balance_due
        payment.status = status

        db.commit()
        db.refresh(payment)
        return payment
    return None
   


def get_payments_by_date_range(db: Session, start_date: datetime, end_date: datetime):
    """
    Get payments made within a specific date range.
    """
    return db.query(payment_models.Payment).filter(
        payment_models.Payment.payment_date.between(start_date, end_date)
    ).all()


  
def delete_payment(db: Session, payment_id: int):
    payment = db.query(payment_models.Payment).filter(payment_models.Payment.id == payment_id).first()
    if payment:
        db.delete(payment)
        db.commit()
  