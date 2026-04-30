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
