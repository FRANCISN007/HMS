from pydantic import BaseModel
from datetime import datetime
from typing import Optional



class PaymentCreateSchema(BaseModel):
    amount_paid: float
    discount_allowed: Optional[float] = 0.0  # New discount field, default to 0.0
    payment_method: str  # E.g., 'credit_card', 'cash', 'bank_transfer'
    payment_date: datetime
    booking_cost: Optional[float]  # Include booking_cost in the schema

    class Config:
        orm_mode = True


class PaymentUpdateSchema(BaseModel):
    guest_name: str
    room_number: str
    amount_paid: Optional[float] = None  # Update the amount if provided
    discount_allowed: Optional[float] = None  # Update discount if provided
    payment_method: Optional[str] = None  # Update the payment method if provided
    payment_date: datetime # Update the payment date if provided
    status: Optional[str] = None  # Update the status (e.g., 'completed', 'pending') if provided
    booking_cost: Optional[float] = None  # Update booking cost if provided

    class Config:
        orm_mode = True
