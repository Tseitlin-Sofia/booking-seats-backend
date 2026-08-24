import uuid
from datetime import time as time_type, timedelta

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cafe import Cafe
from app.models.dish import Dish
from app.models.slot import Slot
from app.models.table import Table


@pytest_asyncio.fixture(scope='function')
async def test_cafe(session: AsyncSession) -> Cafe:
    """Создаёт и возвращает тестовое кафе."""
    unique_suffix = str(uuid.uuid4())[:8]

    cafe = Cafe(
        name=f'Тестовое кафе {unique_suffix}',
        address=f'ул. Тестовая {unique_suffix}, 1',
        phone='+79991234567',
        description='Автотест',
        is_active=True,
    )
    session.add(cafe)
    await session.flush()
    return cafe


@pytest_asyncio.fixture(scope='function')
async def test_dish_500(session: AsyncSession, test_cafe: Cafe) -> Dish:
    """Создаёт блюдо с ценой 500."""
    return await _create_dish(session, test_cafe.id, price=500.0)


@pytest_asyncio.fixture(scope='function')
async def test_dish_350(session: AsyncSession, test_cafe: Cafe) -> Dish:
    """Создаёт блюдо с ценой 350."""
    return await _create_dish(session, test_cafe.id, price=350.0)


async def _create_dish(
    session: AsyncSession,
    cafe_id: int,
    price: float,
) -> Dish:
    """Вспомогательная функция для создания блюда."""
    dish = Dish(
        cafe_id=cafe_id,
        name=f'Тестовое блюдо {str(uuid.uuid4())[:8]}',
        description='Автотест',
        price=price,
        is_available=True,
    )
    session.add(dish)
    await session.flush()
    return dish


@pytest_asyncio.fixture(scope='function')
async def test_slots(session: AsyncSession, test_cafe: Cafe) -> list[dict]:
    """Создаёт и возвращает пару стол+слот для тестов."""
    table = Table(
        cafe_id=test_cafe.id,
        seat_number=4,
        description='Автотест',
        is_active=True,
    )
    session.add(table)

    slot = Slot(
        cafe_id=test_cafe.id,
        start_time=time_type(18, 0),
        end_time=time_type(20, 0),
        is_active=True,
    )
    session.add(slot)

    await session.flush()
    return [{'table_id': table.id, 'slot_id': slot.id}]


@pytest_asyncio.fixture(scope='function')
async def test_date(session: AsyncSession, test_slots: list[dict]) -> str:
    """Возвращает дату в формате YYYY-MM-DD для тестов."""
    # Здесь можно использовать текущую дату или любую другую фиксированную дату
    from datetime import date
    return (date.today() + timedelta(days=1)).isoformat()
