"""Модуль маршрутизатора API."""

from fastapi import APIRouter

from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.cafe import router as cafe_router
from app.api.endpoints.table import router as table_router
from app.api.endpoints.user import router as user_router

main_router = APIRouter()

main_router.include_router(
    auth_router,
    prefix='/auth',
    tags=['Аутентификация'],
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
    user_router,
    prefix='/users',
    tags=['Пользователи'],
)
