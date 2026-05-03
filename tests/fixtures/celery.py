"""Фикстуры для тестирования Celery задач."""

from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import pytest

from app.celery.celery_app import celery_app
from app.models import Cafe, Dish


@pytest.fixture(scope='function')
def celery_config() -> Dict[str, Any]:
    """Настройка Celery для тестов."""
    return {
        'task_always_eager': True,
        'task_eager_propagates': True,
        'broker_transport_options': {'visibility_timeout': 1},
        'result_backend': 'memory',
        'broker_url': 'memory://',
    }


@pytest.fixture(scope='function')
def celery_app_with_config(celery_config) -> Generator:
    """Celery приложение с тестовой конфигурацией."""
    celery_app.conf.update(celery_config)
    yield celery_app
    celery_app.conf.update({
        'task_always_eager': False,
        'task_eager_propagates': False,
    })


@pytest.fixture
def mock_send_email() -> Generator:
    """Мок для функции отправки email."""
    with patch('app.celery.tasks.send_email') as mock:
        yield mock


@pytest.fixture
def mock_loguru_logger() -> Generator:
    """Мок для loguru логгера."""
    with patch('app.celery.base_task.get_logger') as mock:
        mock_logger = MagicMock()
        mock.return_value = mock_logger
        yield mock_logger


@pytest.fixture
def mock_context_vars() -> Generator:
    """Мок для contextvars."""
    with patch('app.celery.base_task.trace_id_ctx') as mock_trace:
        with patch('app.celery.base_task.user_id_ctx') as mock_user:
            with patch('app.celery.base_task.username_ctx') as mock_username:
                yield {
                    'trace_id': mock_trace,
                    'user_id': mock_user,
                    'username': mock_username,
                }


@pytest.fixture
def booking_for_celery(
    test_cafe: Cafe,
    test_dish_500: Dish,
    test_slots: list[dict],
) -> dict:
    """Тестовые данные бронирования для Celery задач."""
    test_slot = test_slots[0]

    return {
        'id': 1,
        'user': {
            'id': 100,
            'username': 'testuser',
            'email': 'test@example.com',
            'phone': '+79991234567',
        },
        'cafe': {
            'id': test_cafe.id,
            'name': test_cafe.name,
            'address': test_cafe.address,
        },
        'table_id': test_slot['table_id'],
        'slot_id': test_slot['slot_id'],
        'booking_date': '2026-05-20',
        'guest_number': 2,
        'status': 'BOOKING',
        'pre_order_items': [
            {
                'dish_id': test_dish_500.id,
                'dish_name': test_dish_500.name,
                'quantity': 2,
                'price_at_order': test_dish_500.price,
            },
        ],
    }
