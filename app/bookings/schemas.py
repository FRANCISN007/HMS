#CheckInSchema
from pydantic import BaseModel, root_validator
from typing import Optional, Literal
from datetime import date
from pydantic import BaseModel, validator
from datetime import datetime, timezone




class BookingSchema(BaseModel):
    """
    Unified schema for both reservations and check-ins.
    """
    room_number: str
    guest_name: str
    arrival_date: date
    departure_date: date
    booking_type: Literal["C", "R"]
    phone_number: str
    #payment_status: Optional[str] = "pending"  # Optional for check-ins
    number_of_days: Optional[int] = None  # Optional for input
    #booking_date: datetime

    class Config:
        orm_mode = True
        
        
    @root_validator(pre=True)
    def calculate_number_of_days(cls, values):
        # Parse dates if they are strings
        arrival_date = values.get("arrival_date")
        departure_date = values.get("departure_date")
        if isinstance(arrival_date, str):
            arrival_date = datetime.strptime(arrival_date, "%Y-%m-%d").date()
            values["arrival_date"] = arrival_date
        if isinstance(departure_date, str):
            departure_date = datetime.strptime(departure_date, "%Y-%m-%d").date()
            values["departure_date"] = departure_date

        # Calculate the number of days
        if arrival_date and departure_date:
            values["number_of_days"] = (departure_date - arrival_date).days
        return values    
        

class BookingSchemaResponse(BaseModel):
    id: int
    room_number: str
    guest_name: str
    arrival_date: date
    departure_date: date
    booking_type: Literal["C", "R"]
    phone_number: str
    status: Optional[str] = "reserved"
    payment_status: Optional[str] = "pending"
    number_of_days: int  # Ensured as part of the response
    booking_cost: Optional[float] = None
    is_checked_out: Optional[bool] = False
    cancellation_reason: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True  # Enable `from_orm` functionality





class UserDisplaySchema(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        orm_mode = True
        

class CheckInUpdateSchema(BaseModel):
    room_number: str
    guest_name: str
    arrival_date: Optional[date]
    departure_date: Optional[date]
    phone_number: str