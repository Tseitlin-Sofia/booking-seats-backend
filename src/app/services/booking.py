"""Сервис для работы с бронированиями."""

from app.schemas.booking import BookingCreate, BookingUpdate
from app.models.booking import Booking
from src.app.api.dependencies import SessionDep



class BookingService:
    """Сервис для работы с бронированиями."""

    def __init__(self, db: SessionDep):
        self.db = db

    def create_booking(self, booking: BookingCreate) -> Booking:
        pass

    def update_booking(self, booking_id: int, booking: BookingUpdate) -> Booking:
        pass

    def get_booking(self, booking_id: int) -> Booking:
        pass

    def get_bookings(self) -> list[Booking]:
        pass

    def delete_booking(self, booking_id: int) -> None:
        pass
