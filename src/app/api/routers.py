"""Модуль маршрутизатора API."""

from fastapi import APIRouter

from app.api.endpoints import cafe_router

main_router = APIRouter()

main_router.include_router(
    cafe_router,
    prefix='/cafes',
    tags=['Кафе'],
)
