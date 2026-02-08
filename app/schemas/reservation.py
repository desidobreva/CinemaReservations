from datetime import datetime
from typing import List
from pydantic import BaseModel, Field

from app.models.reservation import ReservationStatus


class SeatIn(BaseModel):
    seat_row: int = Field(ge=1)
    seat_col: int = Field(ge=1)


class ReservationCreateIn(BaseModel):
    screening_id: int
    seats: List[SeatIn]
    notes: str = ""


class ReservationTicketOut(BaseModel):
    seat_row: int
    seat_col: int


class ReservationOut(BaseModel):
    id: int
    status: ReservationStatus
    screening_id: int
    user_id: int
    created_at: datetime
    notes: str
    tickets: List[ReservationTicketOut]

class ConfirmPaymentIn(BaseModel):
    method: str = "stripe_mock"

class ReservationRescheduleIn(BaseModel):
    new_screening_id: int
    seats: List[SeatIn]
    notes: str = ""