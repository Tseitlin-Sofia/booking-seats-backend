"""Импорты класса Base и всех моделей для Alembic."""

from app.core.db import Base  # noqa
from app.models import Cafe  # noqa
from app.models import Dish  # noqa
from app.models import Table  # noqa
from app.models import Booking, BookingDish, BookingTableSlot, User  # noqa
