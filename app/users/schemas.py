from pydantic import BaseModel
from typing import List
from datetime import datetime
from typing import Optional
from typing import Literal
from decimal import Decimal
from datetime import date

class UserSchema(BaseModel):
    username: str
    password: str
    role: Optional[str] = "user"  # Default role is "user"
    admin_password: Optional[str] = None  # Optional field for admin registration

        
class UserDisplaySchema(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        orm_mode = True


class RoomSchema(BaseModel):
    room_number: str
    room_type: str
    amount: float
    status: Literal["available", "checked-in", "maintenance", "reserved"]  # Updated status options

    class Config:
        orm_mode = True


    class Config:
        orm_mode = True
        
class RoomUpdateSchema(BaseModel):
    room_type: Optional[str] = None
    amount: Optional[int] = None
    status: Optional[Literal["available", "booked", "maintenance", "reserved"]] = None

    class Config:
        orm_mode = True


class ReservationSchema(BaseModel):
    room_number: str  # Use room_number instead of room_id
    guest_name: str
    arrival_date: date
    departure_date: date
    status: Optional[str] = "booked"  # Default value

    class Config:
        orm_mode = True
