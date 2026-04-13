"""Модуль маршрутизатора API."""

from fastapi import APIRouter

from app.api.endpoints import media_router

main_router = APIRouter()

main_router.include_router(
    media_router, prefix='/media', tags=['Media'],
)
