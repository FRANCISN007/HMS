from pydantic import BaseModel
from typing import List
from datetime import datetime
from typing import Optional
from typing import Literal
from decimal import Decimal
from datetime import date

        

class RoomSchema(BaseModel):
    room_number: str
    room_type: str
    amount: float
    status: Literal["available", "checked-in", "maintenance", "reserved"]  # Updated status options

    class Config:
        orm_mode = True
        

class RoomList(BaseModel):
    room_number: str
    room_type: str
    amount: float
    

    class Config:
        orm_mode = True
        
        
class RoomUpdateSchema(BaseModel):
    room_number: str
    room_type: Optional[str] = None
    amount: Optional[int] = None
    status: Optional[Literal["available", "booked", "maintenance", "reserved"]] = None

    class Config:
        orm_mode = True

