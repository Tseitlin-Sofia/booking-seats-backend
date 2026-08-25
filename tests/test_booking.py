# tests/test_booking.py
from datetime import datetime, timedelta
from typing import List

import httpx
import pytest

from app.core.constants import LoggingConstants
from app.core.logging import get_logger, setup_logging
from app.models.cafe import Cafe

logger = get_logger()


@pytest.mark.asyncio
async def test_create_booking_same_table_dates_slots(
    async_client: httpx.AsyncClient,
    capture_sink,
    test_cafe: Cafe,
    test_slots: List[dict],
    test_date: str,
    auth_headers: dict,
):
    """Тестирует создание бронирования на один и тот же стол, дату и слот."""
    captured: List[str] = []
    setup_logging(env='dev', log_level='INFO')
    logger.add(
        capture_sink(captured),
        format=LoggingConstants.LOGGING_FORMAT_STRING,
        )

    # Создаем бронирование
    booking_payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'booking_date': test_date,
        'guest_number': 1,
    }

    response = await async_client.post(
        "/bookings/",
        json=booking_payload,
        headers=auth_headers,
    )
    assert response.status_code == 201, f"Unexpected status code: {response.status_code}, response: {response.text}"
    # Пытаемся создать бронирование на тот же стол, дату и слот
    response_duplicate = await async_client.post(
        "/bookings/",
        json=booking_payload,
        headers=auth_headers,
    )
    assert response_duplicate.status_code == 422, f"Expected 422 for duplicate booking, got {response_duplicate.status_code}, response: {response_duplicate.text}"


@pytest.mark.asyncio
async def test_create_booking_in_adjacent_slot_succeeds(
    async_client: httpx.AsyncClient,
    test_cafe: Cafe,
    test_back_to_back_slots: List[dict],
    test_date: str,
    auth_headers: dict,
):
    """Тестирует создание бронирования на один и тот же стол, дату, но в соседний слот."""
    # Создаем бронирование в первом слоте
    booking_payload_first_slot = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_back_to_back_slots[0]['table_id'],
                'slot_id': test_back_to_back_slots[0]['slot_id'],
            },
        ],
        'booking_date': test_date,
        'guest_number': 1,
    }

    response_first_slot = await async_client.post(
        "/bookings/",
        json=booking_payload_first_slot,
        headers=auth_headers,
    )
    assert response_first_slot.status_code == 201, f"Unexpected status code for first slot booking: {response_first_slot.status_code}, response: {response_first_slot.text}"

    # Создаем бронирование во втором слоте (соседний слот)
    booking_payload_second_slot = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_back_to_back_slots[1]['table_id'],
                'slot_id': test_back_to_back_slots[1]['slot_id'],  # Используем соседний слот
            },
        ],
        'booking_date': test_date,
        'guest_number': 1,
    }

    response_second_slot = await async_client.post(
        "/bookings/",
        json=booking_payload_second_slot,
        headers=auth_headers,
    )
    assert response_second_slot.status_code == 201, f"Unexpected status code for second slot booking: {response_second_slot.status_code}, response: {response_second_slot.text}"


@pytest.mark.asyncio
async def test_create_booking_same_slot_another_date(
    async_client: httpx.AsyncClient,
    test_cafe: Cafe,
    test_slots: List[dict],
    test_date: str,
    auth_headers: dict,
):
    """Тестирует создание бронирования на один и тот же стол и слот, но на другую дату."""
    # Создаем бронирование на первую дату
    booking_payload_first_date = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'booking_date': test_date,
        'guest_number': 1,
    }

    response_first_date = await async_client.post(
        "/bookings/",
        json=booking_payload_first_date,
        headers=auth_headers,
    )
    assert response_first_date.status_code == 201, f"Unexpected status code for first date booking: {response_first_date.status_code}, response: {response_first_date.text}"

    # Создаем бронирование на вторую дату (следующий день)
    next_day = (datetime.strptime(test_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    booking_payload_second_date = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],  # Используем тот же слот
            },
        ],
        'booking_date': next_day,
        'guest_number': 1,
    }

    response_second_date = await async_client.post(
        "/bookings/",
        json=booking_payload_second_date,
        headers=auth_headers,
    )
    assert response_second_date.status_code == 201, f"Unexpected status code for second date booking: {response_second_date.status_code}, response: {response_second_date.text}"


@pytest.mark.asyncio
async def test_create_booking_for_some_tables(
    async_client: httpx.AsyncClient,
    test_cafe: Cafe,
    test_multiple_tables_slot: List[dict],
    test_date: str,
    auth_headers: dict,
):
    """Тестируем создание одного бронирования на несколько столов в одном и том же слоте и дате."""
    booking_payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_multiple_tables_slot[0]['table_id'],
                'slot_id': test_multiple_tables_slot[0]['slot_id'],
            },
        ],
        'booking_date': test_date,
        'guest_number': 1,
    }
    response_second_date = await async_client.post(
            "/bookings/",
            json=booking_payload,
            headers=auth_headers,
        )
    assert response_second_date.status_code == 201, f"Unexpected status code for second date booking: {response_second_date.status_code}, response: {response_second_date.text}"


@pytest.mark.asyncio
async def test_create_booking_exceeding_table_capacity(
    async_client: httpx.AsyncClient,
    test_cafe: Cafe,
    test_slots: List[dict],
    test_date: str,
    auth_headers: dict,
):
    """Тестируем создание бронирования с количеством гостей, превышающим вместимость стола."""
    # Предположим, что стол рассчитан на 4 человека
    booking_payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'booking_date': test_date,
        'guest_number': 5,  # Превышаем вместимость стола
    }
    response = await async_client.post(
        "/bookings/",
        json=booking_payload,
        headers=auth_headers,
    )
    assert response.status_code == 422, f"Expected 422 for exceeding table capacity, got {response.status_code}, response: {response.text}"


@pytest.mark.asyncio
async def test_create_slot_from_another_cafe(
    async_client: httpx.AsyncClient,
    test_cafe: Cafe,
    test_slots: List[dict],
    test_date: str,
    auth_headers: dict,
):
    """Тестируем создание бронирования на слот, принадлежащий другому кафе."""
    # Создаем фиктивное кафе
    fake_cafe = Cafe(
        name="Fake Cafe",
        address="123 Fake St",
        description="Fake cafe for testing")
    # Предположим, что мы добавили его в базу данных и получили его ID
    fake_cafe_id = 999

    booking_payload = {
        'cafe_id': fake_cafe_id,  # Используем ID фиктивного кафе
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],  # Используем стол из фейкового кафе
                'slot_id': test_slots[0]['slot_id'],  # Используем слот из фейкового кафе
            },
        ],
        'booking_date': test_date,
        'guest_number': 1,
    }
    response = await async_client.post(
        "/bookings/",
        json=booking_payload,
        headers=auth_headers,
    )
    assert response.status_code == 404, f"Expected 404 for booking in another cafe's slot, got {response.status_code}, response: {response.text}"


@pytest.mark.asyncio
async def test_deactivated_booking_opens_slot(
    async_client: httpx.AsyncClient,
    test_cafe: Cafe,
    test_slots: List[dict],
    test_date: str,
    auth_headers: dict,
):
    """Тестируем, что деактивация бронирования освобождает слот для нового бронирования."""
    # Создаем бронирование
    booking_payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'booking_date': test_date,
        'guest_number': 1,
    }
    response_create = await async_client.post(
        "/bookings/",
        json=booking_payload,
        headers=auth_headers,
    )
    assert response_create.status_code == 201, f"Unexpected status code for booking creation: {response_create.status_code}, response: {response_create.text}"

    # Деактивируем бронирование
    booking_id = response_create.json()['id']
    response_deactivate = await async_client.patch(
        f"/bookings/{booking_id}",
        json={"is_active": False},
        headers=auth_headers,
    )
    assert response_deactivate.status_code == 200, f"Unexpected status code for booking deactivation: {response_deactivate.status_code}, response: {response_deactivate.text}"

    # Пытаемся создать новое бронирование на тот же стол и слот после деактивации предыдущего
    response_recreate = await async_client.post(
        "/bookings/",
        json=booking_payload,
        headers=auth_headers,
    )
    assert response_recreate.status_code == 201, f"Expected 201 for new booking after deactivation, got {response_recreate.status_code}, response: {response_recreate.text}"
