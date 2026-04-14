"""Модуль маршрутизатора API."""

from fastapi import APIRouter

from app.api.endpoints.table import router as table_router
from app.api.endpoints import user_router

main_router = APIRouter()

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