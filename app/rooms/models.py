   
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, unique=True, nullable=False)
    room_type = Column(String(50))
    amount = Column(Integer)
    status = Column(String(50))

    # Establish relationship with reservations
    reservations = relationship("Reservation", back_populates="room")
    #check_in = relationship("Check_in", back_populates="room")
    check_in = relationship("Check_in", back_populates="room", cascade="all, delete-orphan")

