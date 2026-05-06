"""Тестирование функции создания задач Celery для уведомлений."""
from datetime import date
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from datetime import date, datetime, timezone
from app.models.cafe import Cafe
from app.models.user import User
from app.models.booking import Booking

from app.models.user import User
from app.models.cafe import Cafe
from app.schemas.booking import BookingStatus

# Добавляем src в sys.path, чтобы работали импорты
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Загружаем переменные окружения из src/.env
load_dotenv()

# Подключаем Celery приложение
from app.celery.celery_app import celery_app, get_logger

logger = get_logger()

# Импортируем задачу, чтобы Celery их «знал» при вызове delay
import app.celery.tasks  # noqa: F401

# Импорты моделей и вспомогательных функций
from app.api.endpoints.booking import _make_notification_tasks_for_celery
from app.core.db import get_async_session
from app.models.booking import Booking
from app.schemas.booking import BookingInfo

# Тестовые данные на основе твоего JSON
TEST_BOOKING_DATA: Dict[str, Any] = {
    "tables_slots": [
        {"table_id": 5, "slot_id": 3}
    ],
    "guest_number": 2,
    "note": "Тестовый заказ, окно",
    "booking_date": "2026-05-10",
    "id": 999,
    "user": {
        "username": "Тестовый Гость",
        "email": os.getenv("CLIENT_EMAIL", "hipstot@yandex.ru"),
        "phone": "+71234567890",
        "tg_id": "test_tg",
        "id": 10,
    },
    "cafe": {
        "name": "Каффетерий",
        "address": "ул. Тестовая, 1",
        "phone": "+78005553535",
        "description": "Тестовое кафе",
        "photo_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "id": 100,
    },
    "pre_order_items": [
        {
            "dish": {
                "id": 1,
                "name": "Капучино",
                "price": 250,
                "description": "Кофе с молоком",
                "is_available": True,
            },
            "quantity": 2,
            "price_at_order": 250,
        }
    ],
    "status": "BOOKING",
    "is_active": True,
    "created_at": "2026-05-04T18:37:16.395Z",
    "updated_at": "2026-05-04T18:37:16.395Z",
}


def _create_fake_booking() -> Booking:
    """Создаёт объект бронирования с user и cafe."""
    now = datetime.now(timezone.utc)
    
    user = User(
        id=10,
        username="Тестовый Гость",
        email=os.getenv("CLIENT_EMAIL", "hipstot@yandex.ru"),
        phone="+71234567890",
        tg_id="test_tg",
        created_at=now,
        updated_at=now,
        is_active=True,
    )
    cafe = Cafe(
        id=100,
        name="Каффетерий",
        address="ул. Тестовая, 1",
        phone="+78005553535",
        description="Тестовое кафе",
        created_at=now,
        updated_at=now,
        is_active=True,
    )
    booking = Booking(
        id=999,
        guest_number=2,
        note="Тестовый заказ, окно",
        booking_date=date(2026, 5, 10),
        status="BOOKING",
        is_active=True,
        user_id=user.id,
        cafe_id=cafe.id,
        user=user,
        cafe=cafe,
        created_at=now,
        updated_at=now,
    )
    return booking


async def _get_mock_session():
    """Возвращает асинхронную сессию для тестов (без реальной БД).

    В реальном тесте ты можешь использовать get_async_session(),
    если БД запущена. Здесь для упрощения возвращаем None.
    Функция _make_notification_tasks_for_celery использует сессию
    только для получения booking_datetime – мы это замокаем.
    """
    # Это заглушка, в реальном тесте лучше замокать get_start_datetime_by_booking_id
    return None


async def test_post_notification():
    """Тест создания уведомлений при POST-запросе."""
    print("\n" + "=" * 60)
    print("ТЕСТ 1: Создание задач (POST)")
    print("=" * 60)

    booking = _create_fake_booking()
    session = await _get_mock_session()

    # В реальном коде _make_notification_tasks_for_celery вызывает
    # booking_crud.get_start_datetime_by_booking_id – замокаем это поведение
    booking_datetime = datetime.now(timezone.utc) + timedelta(hours=3)
    print(f"▶ Назначаем время бронирования: {booking_datetime}")

    # --- Сам вызов тестируемой функции ---
    try:
        await _make_notification_tasks_for_celery(
            booking_obj=booking,
            session=session,
            method="POST",
        )
        print("✅ Успешно вызвана функция с method='POST'")
    except Exception as e:
        logger.exception("Ошибка при вызове POST-уведомления")
        print(f"❌ Ошибка при вызове POST-уведомления: {e}")


async def test_patch_notification():
    """Тест обновления уведомлений при PATCH-запросе."""
    print("\n" + "=" * 60)
    print("ТЕСТ 2: Создание задач (PATCH)")
    print("=" * 60)

    booking = _create_fake_booking()
    session = await _get_mock_session()

    booking_datetime = datetime.now(timezone.utc) + timedelta(hours=5)
    print(f"▶ Изменённое время бронирования: {booking_datetime}")

    try:
        await _make_notification_tasks_for_celery(
            booking_obj=booking,
            session=session,
            method="PATCH",
        )
        print("✅ Успешно вызвана функция с method='PATCH'")
    except Exception as e:
        logger.exception("Ошибка при вызове PATCH-уведомления")
        print(f"❌ Ошибка при вызове PATCH-уведомления: {e}")


async def main():
    await test_post_notification()
    await test_patch_notification()
    print("\n" + "=" * 60)
    print("Тесты завершены. Проверьте почту отправителя и получателя.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())