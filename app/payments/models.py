from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey('bookings.id'))  # Foreign key to bookings table
    room_number = Column(String, index=True)
    guest_name = Column(String, index=True)
    booking_cost = Column(Float)  # Add the booking_cost column to Payment table
    amount_paid = Column(Float)
    discount_allowed = Column(Float, default=0.0)  # Discount allowed on the payment
    balance_due = Column(Float, default=0.0)
    payment_method = Column(String)
    payment_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")
    
    # Foreign key relationship to the booking
    booking = relationship("Booking", back_populates="payments")