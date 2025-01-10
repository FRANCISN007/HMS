# models.py
from sqlalchemy import event
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean, DateTime, Float
from app.database import Base
from datetime import datetime



class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, ForeignKey("rooms.room_number", ondelete="CASCADE"), nullable=False)
    guest_name = Column(String, nullable=False)
    room_price = Column(Float, nullable=False)
    arrival_date = Column(Date, nullable=False)
    departure_date = Column(Date, nullable=False)
    number_of_days = Column(Integer, nullable=False)
    booking_cost = Column(Float, nullable=True)
    booking_type = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    status = Column(String, default="reserved")
    payment_status = Column(String, default="pending")
    booking_date = Column(DateTime, default=datetime.utcnow)
    is_checked_out = Column(Boolean, default=False)
    cancellation_reason = Column(String, nullable=True)
    deleted = Column(Boolean, default=False)  # Soft delete flag

    # Relationships
    room = relationship("Room", back_populates="bookings")
    payments = relationship("Payment", back_populates="booking")

# Event listener
@event.listens_for(Booking, "before_insert")
@event.listens_for(Booking, "before_update")
def set_number_of_days(mapper, connection, target):
    if target.arrival_date and target.departure_date:
        target.number_of_days = (target.departure_date - target.arrival_date).days