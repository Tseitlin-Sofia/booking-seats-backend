# tests/test_preorder.py
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List

import httpx
import jwt
import pytest
from pwdlib import PasswordHash

from app.core.config import settings
from app.core.constants import LoggingConstants
from app.core.logging import get_logger, setup_logging
from app.core.user import AuthService
from app.models.cafe import Cafe
from app.models.dish import Dish
from app.models.user import User
from tests.conftest import LOG_WRITE_DELAY_SEC

logger = get_logger()


@pytest.mark.asyncio
async def test_create_booking_with_pre_order_success(
    async_client: httpx.AsyncClient,
    capture_sink,
    test_cafe,
    test_dish_350,
    test_dish_500,
    test_slots,
    auth_headers: dict,
) -> None:
    """Успешное создание бронирования с предзаказом автор. пользователем.

    Проверяет:
    - Статус-код 201.
    - Присутствие pre_order_items в ответе.
    - Количество позиций предзаказа равно 2.
    - Цена блюда зафиксирована на момент заказа.
    - Наличие записи в логах о добавлении предзаказа.
    """
    captured: List[str] = []
    setup_logging(env='dev', log_level='INFO')
    logger.add(
        capture_sink(captured),
        format=LoggingConstants.LOGGING_FORMAT_STRING,
    )

    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 2,
        'booking_date': '2026-05-20',
        'pre_order_items': [
            {'dish_id': test_dish_500.id, 'quantity': 2},
            {'dish_id': test_dish_350.id, 'quantity': 1},
        ],
    }

    response = await async_client.post(
        '/bookings/',
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert 'pre_order_items' in data
    assert len(data['pre_order_items']) == 2
    assert data['pre_order_items'][0]['price_at_order'] == 500.0

    await asyncio.sleep(LOG_WRITE_DELAY_SEC)
    assert any(
        'Предзаказ блюд успешно добавлен к бронированию.' in log
        for log in captured
    )


@pytest.mark.asyncio
async def test_unauthorized_user_cannot_create_booking(
    async_client: httpx.AsyncClient,
    test_cafe,
    test_slots,
) -> None:
    """Попытка создать бронирование с предзаказом неавтор. пользователем.

    Проверяет, что запрос без токена авторизации возвращает статус-код 403.
    """
    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 1,
        'booking_date': '2026-05-20',
        'pre_order_items': [{'dish_id': 999, 'quantity': 1}],
    }

    response = await async_client.post('/bookings/', json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_booking_with_single_pre_order_item(
    async_client,
    test_cafe,
    test_dish_500,
    test_slots,
    auth_headers,
) -> None:
    """Успешное создание бронирования с одной позицией в предзаказе.

    Проверяет:
    - Статус-код 201.
    - Ровно одна позиция в pre_order_items.
    - Корректность цены и количества.
    """
    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 2,
        'booking_date': '2026-05-20',
        'pre_order_items': [{'dish_id': test_dish_500.id, 'quantity': 1}],
    }
    response = await async_client.post(
        '/bookings/',
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data['pre_order_items']) == 1
    assert data['pre_order_items'][0]['price_at_order'] == 500.0
    assert data['pre_order_items'][0]['quantity'] == 1


@pytest.mark.asyncio
async def test_create_booking_with_multiple_quantities(
    async_client,
    test_cafe,
    test_dish_350,
    test_slots,
    auth_headers,
) -> None:
    """Успешное создание бронирования с количеством блюда больше одного.

    Проверяет, что количество порций корректно сохраняется в ответе.
    """
    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 3,
        'booking_date': '2026-05-20',
        'pre_order_items': [{'dish_id': test_dish_350.id, 'quantity': 5}],
    }
    response = await async_client.post(
        '/bookings/',
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data['pre_order_items'][0]['quantity'] == 5


@pytest.mark.asyncio
async def test_create_booking_without_pre_order(
    async_client,
    test_cafe,
    test_slots,
    auth_headers,
) -> None:
    """Успешное создание бронирования без позиций предзаказа.

    Проверяет, что бронирование создаётся и pre_order_items либо отсутствует,
    либо является пустым списком.
    """
    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 2,
        'booking_date': '2026-05-20',
    }
    response = await async_client.post(
        '/bookings/',
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data['pre_order_items'] is None or len(data['pre_order_items']) == 0


@pytest.mark.asyncio
async def test_get_booking_returns_pre_order_items(
    async_client,
    test_cafe,
    test_dish_500,
    test_slots,
    auth_headers,
) -> None:
    """Получение бронирования по ID должно включать позиции предзаказа.

    Проверяет, что GET-запрос возвращает полную информацию о предзаказе.
    """
    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 2,
        'booking_date': '2026-05-20',
        'pre_order_items': [{'dish_id': test_dish_500.id, 'quantity': 1}],
    }
    create_resp = await async_client.post(
        '/bookings/',
        json=payload,
        headers=auth_headers,
    )
    booking_id = create_resp.json()['id']

    get_resp = await async_client.get(
        f'/bookings/{booking_id}',
        headers=auth_headers,
    )
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert 'pre_order_items' in data
    assert len(data['pre_order_items']) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'quantity, expected_status',
    [
        (0, 422),
        (-1, 422),
        (999999, 422),
    ],
)
async def test_pre_order_invalid_quantity(
    async_client,
    test_cafe,
    test_dish_500,
    test_slots,
    auth_headers,
    quantity,
    expected_status,
) -> None:
    """Валидация недопустимых значений количества блюд в предзаказе.

    Проверяет, что нулевое, отрицательное и чрезмерно большое количество
    отклоняются сервером с кодом 422.
    """
    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 2,
        'booking_date': '2026-05-20',
        'pre_order_items': [
            {'dish_id': test_dish_500.id, 'quantity': quantity},
        ],
    }
    response = await async_client.post(
        '/bookings/',
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == expected_status


@pytest.mark.asyncio
async def test_pre_order_empty_items_list(
    async_client,
    test_cafe,
    test_slots,
    auth_headers,
) -> None:
    """Создание бронирования с пустым списком предзаказа должно работать.

    Проверяет, что передача пустого массива pre_order_items не вызывает ошибки
    и бронирование создаётся со статусом 201.
    """
    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 2,
        'booking_date': '2026-05-20',
        'pre_order_items': [],
    }
    response = await async_client.post(
        '/bookings/',
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_pre_order_duplicate_dishes(
    async_client,
    test_cafe,
    test_dish_500,
    test_slots,
    auth_headers,
) -> None:
    """Проверка обработки дублирующихся идентификаторов блюд в предзаказе.

    Отправляет одно и то же блюдо дважды и проверяет, что сервер либо
    корректно обрабатывает дубликат, либо возвращает ошибку валидации.
    """
    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 2,
        'booking_date': '2026-05-20',
        'pre_order_items': [
            {'dish_id': test_dish_500.id, 'quantity': 1},
            {'dish_id': test_dish_500.id, 'quantity': 2},
        ],
    }
    response = await async_client.post(
        '/bookings/',
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code in [201, 422]


@pytest.mark.asyncio
async def test_pre_order_nonexistent_dish(
    async_client,
    test_cafe,
    test_slots,
    auth_headers,
) -> None:
    """Попытка заказать несуществующее блюдо должна возвращать ошибку 422.

    Проверяет, что сервер возвращает соответствующий статус-код и
    сообщение о том, что блюда не найдены.
    """
    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 2,
        'booking_date': '2026-05-20',
        'pre_order_items': [{'dish_id': 99999, 'quantity': 1}],
    }
    response = await async_client.post(
        '/bookings/',
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert 'не найдены' in response.json()['detail'].lower()


@pytest.mark.asyncio
async def test_pre_order_unavailable_dish(
    async_client,
    test_cafe,
    test_slots,
    session,
    auth_headers,
) -> None:
    """Попытка заказать недоступное блюдо должна возвращать ошибку 422.

    Создаёт блюдо с флагом is_available=False и проверяет,
    что сервер отклоняет его добавление в предзаказ.
    """
    dish = Dish(
        cafe_id=test_cafe.id,
        name='Недоступное блюдо',
        price=100.0,
        is_available=False,
    )
    session.add(dish)
    await session.flush()

    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 2,
        'booking_date': '2026-05-20',
        'pre_order_items': [{'dish_id': dish.id, 'quantity': 1}],
    }
    response = await async_client.post(
        '/bookings/',
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert 'недоступны' in response.json()['detail'].lower()


@pytest.mark.asyncio
async def test_pre_order_dish_from_other_cafe(
    async_client,
    test_cafe,
    test_slots,
    session,
    auth_headers,
) -> None:
    """Попытка заказать блюдо из другого кафе должна возвращать ошибку 422.

    Создаёт второе кафе с собственным блюдом и проверяет, что сервер
    не позволяет добавить его в предзаказ к первому кафе.
    """
    other_cafe = Cafe(
        name='Другое кафе',
        address='Другой адрес',
        phone='+79990000000',
        is_active=True,
    )
    session.add(other_cafe)
    await session.flush()

    other_dish = Dish(
        cafe_id=other_cafe.id,
        name='Чужое блюдо',
        price=200.0,
        is_available=True,
    )
    session.add(other_dish)
    await session.flush()

    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 2,
        'booking_date': '2026-05-20',
        'pre_order_items': [{'dish_id': other_dish.id, 'quantity': 1}],
    }
    response = await async_client.post(
        '/bookings/',
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert 'не принадлежат' in response.json()['detail'].lower()


@pytest.mark.asyncio
async def test_regular_user_can_see_only_own_booking_pre_order(
    async_client,
    test_cafe,
    test_dish_500,
    test_slots,
    auth_headers,
    session,
) -> None:
    """Пользователь не может просматривать чужие бронирования с предзаказом.

    Создаёт бронирование одним пользователем и проверяет, что второй
    пользователь получает ошибку 403 при попытке его просмотра.
    """
    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 2,
        'booking_date': '2026-05-20',
        'pre_order_items': [{'dish_id': test_dish_500.id, 'quantity': 1}],
    }
    resp = await async_client.post(
        '/bookings/',
        json=payload,
        headers=auth_headers,
    )
    booking_id = resp.json()['id']

    ph = PasswordHash.recommended()
    user2 = User(
        username='other_user_test',
        email='other@test.com',
        password_hash=ph.hash('Test123'),
        role='user',
        is_active=True,
    )
    session.add(user2)
    await session.flush()

    token2 = AuthService.create_token(user2.id, user2.role)
    headers2 = {'Authorization': f'Bearer {token2}'}

    get_resp = await async_client.get(
        f'/bookings/{booking_id}',
        headers=headers2,
    )
    assert get_resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_see_any_booking_pre_order(
    async_client,
    test_cafe,
    test_dish_500,
    test_slots,
    auth_headers,
    session,
) -> None:
    """Администратор может просматривать любое бронирование с предзаказом.

    Создаёт бронирование обычным пользователем и проверяет, что
    администратор успешно получает его с кодом 200 и видит позиции предзаказа.
    """
    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 2,
        'booking_date': '2026-05-20',
        'pre_order_items': [{'dish_id': test_dish_500.id, 'quantity': 1}],
    }
    resp = await async_client.post(
        '/bookings/',
        json=payload,
        headers=auth_headers,
    )
    booking_id = resp.json()['id']

    ph = PasswordHash.recommended()
    admin = User(
        username='admin_test',
        email='admin@test.com',
        password_hash=ph.hash('Admin123'),
        role='admin',
        is_active=True,
    )
    session.add(admin)
    await session.flush()

    admin_token = AuthService.create_token(admin.id, admin.role)
    admin_headers = {'Authorization': f'Bearer {admin_token}'}

    get_resp = await async_client.get(
        f'/bookings/{booking_id}',
        headers=admin_headers,
    )
    assert get_resp.status_code == 200
    assert len(get_resp.json()['pre_order_items']) == 1


@pytest.mark.asyncio
async def test_create_booking_with_pre_order_unauthorized(
    async_client: httpx.AsyncClient,
    test_cafe,
    test_dish_350,
    test_dish_500,
    test_slots,
) -> None:
    """Неавтор. пользователь не может создать бронирование с предзаказом.

    Проверяет, что запрос без заголовка Authorization возвращает статус-код 403
    и тело ответа содержит поле detail.
    """
    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 2,
        'booking_date': '2026-05-20',
        'pre_order_items': [
            {'dish_id': test_dish_500.id, 'quantity': 2},
            {'dish_id': test_dish_350.id, 'quantity': 1},
        ],
    }

    response = await async_client.post(
        '/bookings/',
        json=payload,
    )

    assert response.status_code == 403
    assert 'detail' in response.json()


@pytest.mark.asyncio
async def test_create_booking_unauthorized_without_pre_order(
    async_client: httpx.AsyncClient,
    test_cafe,
    test_slots,
) -> None:
    """Неавтор. пользователь не может создать бронирование без предзаказа.

    Проверяет, что даже без позиций предзаказа запрос без токена авторизации
    возвращает статус-код 403.
    """
    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 3,
        'booking_date': '2026-05-20',
    }

    response = await async_client.post(
        '/bookings/',
        json=payload,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_booking_with_invalid_token(
    async_client: httpx.AsyncClient,
    test_cafe,
    test_dish_500,
    test_slots,
) -> None:
    """Попытка создать бронирование с некорректным JWT-токеном.

    Проверяет, что сервер возвращает 401 при передаче невалидного токена
    и тело ответа содержит поле detail.
    """
    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 2,
        'booking_date': '2026-05-20',
        'pre_order_items': [
            {'dish_id': test_dish_500.id, 'quantity': 1},
        ],
    }

    response = await async_client.post(
        '/bookings/',
        json=payload,
        headers={'Authorization': 'Bearer invalid_token_here'},
    )

    assert response.status_code == 401
    assert 'detail' in response.json()


@pytest.mark.asyncio
async def test_create_booking_with_expired_token(
    async_client: httpx.AsyncClient,
    test_cafe,
    test_dish_350,
    test_slots,
) -> None:
    """Попытка создать бронирование с истёкшим JWT-токеном.

    Генерирует токен с истёкшим сроком действия и проверяет, что сервер
    возвращает 401 с сообщением об истечении токена.
    """
    expired_token = jwt.encode(
        {
            'sub': '1',
            'role': 'user',
            'iat': datetime.now(timezone.utc) - timedelta(hours=2),
            'exp': datetime.now(timezone.utc) - timedelta(hours=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 2,
        'booking_date': '2026-05-20',
        'pre_order_items': [
            {'dish_id': test_dish_350.id, 'quantity': 1},
        ],
    }

    response = await async_client.post(
        '/bookings/',
        json=payload,
        headers={'Authorization': f'Bearer {expired_token}'},
    )

    assert response.status_code == 401
    assert 'expired' in response.json()['detail'].lower()


@pytest.mark.asyncio
async def test_create_booking_without_auth_header(
    async_client: httpx.AsyncClient,
    test_cafe,
    test_slots,
) -> None:
    """Попытка создать бронирование при отсутствии заголовка Authorization.

    Проверяет, что сервер возвращает 403,
    когда заголовок Authorization не передан.
    """
    payload = {
        'cafe_id': test_cafe.id,
        'tables_slots': [
            {
                'table_id': test_slots[0]['table_id'],
                'slot_id': test_slots[0]['slot_id'],
            },
        ],
        'guest_number': 1,
        'booking_date': '2026-05-20',
    }

    response = await async_client.post(
        '/bookings/',
        json=payload,
    )

    assert response.status_code == 403
