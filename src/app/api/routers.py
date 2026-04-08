"""Модуль маршрутизатора API."""

from fastapi import APIRouter


main_router = APIRouter()

# main_router.include_router(
#     meeting_room_router, prefix='/meeting_rooms', tags=['Meeting Rooms']
# )
