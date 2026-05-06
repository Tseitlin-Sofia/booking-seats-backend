from typing import Callable, Optional

import pytest

from app.schemas.dish import PreOrderItemCreate


@pytest.fixture
def build_preorder_payload() -> Callable:
    """Фабрика для построения тестового payload для создания бронирования."""

    def _build(
        cafe_id: int,
        table_id: int,
        slot_id: int,
        booking_date: str,
        items: Optional[list[PreOrderItemCreate]] = None,
    ) -> dict:
        payload = {
            'cafe_id': cafe_id,
            'tables_slots': [{'table_id': table_id, 'slot_id': slot_id}],
            'guest_number': 2,
            'booking_date': booking_date,
        }
        if items:
            payload['pre_order_items'] = [item.model_dump() for item in items]
        return payload

    return _build


@pytest.fixture
def booking_payload_without_preorder() -> dict:
    """Базовый payload для создания бронирования без предзаказа."""
    return {
        'tables_slots': [],
        'guest_number': 2,
        'booking_date': '2026-05-20',
    }


@pytest.fixture
def booking_payload_with_preorder() -> dict:
    """Базовый payload для создания бронирования с предзаказом."""
    return {
        'tables_slots': [],
        'guest_number': 2,
        'booking_date': '2026-05-20',
        'pre_order_items': [],
    }


@pytest.fixture
def update_preorder_payload() -> Callable:
    """Фабрика для построения payload обновления предзаказа."""

    def _build(items: Optional[list[dict]] = None) -> dict:
        payload = {}
        if items is not None:
            payload['pre_order_items'] = items
        return payload

    return _build


@pytest.fixture
def invalid_preorder_items() -> dict:
    """Невалидные данные для предзаказа."""
    return {
        'nonexistent': [{'dish_id': 99999, 'quantity': 1}],
        'zero_quantity': [{'dish_id': 1, 'quantity': 0}],
        'negative_quantity': [{'dish_id': 1, 'quantity': -1}],
        'too_large_quantity': [{'dish_id': 1, 'quantity': 999999}],
    }
