"""Сервис для работы с бронированиями."""

from src.app.api.dependencies import SessionDep


# TODO: Вероятно стоит перенести сюда часть работы с бронированиями
#  (из endpoints) и добавить ворнинг на guest_number
class BookingService:
    """Сервис для работы с бронированиями."""

    def __init__(self, db: SessionDep) -> None:
        """Инициализация сервиса с подключением к базе данных."""
        self.db = db
