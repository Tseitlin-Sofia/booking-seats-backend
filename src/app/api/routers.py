"""Модуль маршрутизатора API."""

from fastapi import APIRouter

from app.api.endpoints.action import router as action_router
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.booking import router as booking_router
from app.api.endpoints.cafe import router as cafe_router
from app.api.endpoints.dish import router as dish_router
from app.api.endpoints.media import router as media_router
from app.api.endpoints.slot import router as slot_router
from app.api.endpoints.table import router as table_router
from app.api.endpoints.user import router as user_router

main_router = APIRouter()

main_router.include_router(
    media_router,
    prefix='/media',
    tags=['Медиа'],
)
main_router.include_router(
    action_router,
    prefix='/actions',
    tags=['Акции'],
)
main_router.include_router(
    cafe_router,
    prefix='/cafes',
    tags=['Кафе'],
)
main_router.include_router(
    table_router,
    prefix='/cafes/{cafe_id}/tables',
    tags=['Столы'],
)
main_router.include_router(
    slot_router,
    prefix='/cafes/{cafe_id}/timeslots',
    tags=['Слоты'],
)
main_router.include_router(
    dish_router,
    prefix='/cafes/{cafe_id}/dishes',
    tags=['Блюда'],
)
main_router.include_router(
    user_router,
    prefix='/users',
    tags=['Пользователи'],
)
main_router.include_router(
    auth_router,
    prefix='/auth',
    tags=['Аутентификация'],
)
main_router.include_router(
    booking_router,
    prefix='/bookings',
    tags=['Бронирования'],
)
