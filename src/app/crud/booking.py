"""CRUD операции для бронирования."""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import BookingConstants as Constants
from app.core.logging import get_logger
from app.crud.base import CRUDBase
from app.crud.slot import slot_crud
from app.crud.table import table_crud
from app.models import (
    Booking,
    BookingDish,
    BookingTableSlot,
    Dish,
    Slot,
    Table,
)
from app.schemas.booking import BookingStatus
from app.schemas.dish import PreOrderItemCreate

logger = get_logger()


class BookingCRUD(CRUDBase):
    """CRUD операции для бронирования."""

    def booking_full_load_options(self) -> list:
        """Загружает все необходимые связи для BookingInfo."""
        return [
            selectinload(Booking.user),
            selectinload(Booking.cafe),
            selectinload(Booking.tables_slots),
            selectinload(Booking.pre_order_items).selectinload(
                BookingDish.dish,
            ),
        ]

    async def get_bookings(
        self,
        session: AsyncSession,
        show_active: Optional[bool] = True,
        cafe_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> list[Booking]:
        """Получает бронирования."""
        stmt = select(Booking).options(
            *self.booking_full_load_options(),
        )
        if show_active is not None:
            stmt = stmt.where(Booking.is_active == show_active)
        if cafe_id is not None:
            stmt = stmt.where(Booking.cafe_id == cafe_id)
        if user_id is not None:
            stmt = stmt.where(Booking.user_id == user_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def add_pre_order_items(
        self,
        booking_id: int,
        items: list[PreOrderItemCreate],
        dishes_map: dict[int, Dish],
        session: AsyncSession,
    ) -> None:
        """Создаёт записи предзаказа и привязывает их к бронированию."""
        booking_dishes = [
            BookingDish(
                booking_id=booking_id,
                dish_id=item.dish_id,
                quantity=item.quantity,
                price_at_order=dishes_map[item.dish_id].price,
            )
            for item in items
        ]
        session.add_all(booking_dishes)
        await session.commit()

        logger.info(
            'Предзаказ блюд успешно добавлен к бронированию. '
            f'booking_id: {booking_id}, '
            f'items_count: {len(items)}',
        )

    async def get_start_datetime_by_booking_id(
        self,
        booking_id: int,
        session: AsyncSession,
    ) -> datetime:
        """Получает дату и время начала бронирования по id бронирования."""
        booking = await self.get(booking_id, session)
        if not booking:
            raise ValueError(Constants.BOOKING_NOT_FOUND)
        booking_date = booking.booking_date
        stmt = select(BookingTableSlot).where(
            BookingTableSlot.booking_id == booking_id,
            BookingTableSlot.is_active,
        )
        table_slots = await session.execute(stmt)
        booking_time = min(
            [
                table_slot.slot.start_time
                for table_slot
                in table_slots.scalars().all()
            ],
        )
        return datetime.combine(booking_date, booking_time)

    async def get_start_datetime_by_slots_and_date(
        self,
        tables_slots: list[dict[str, int]],
        booking_date: date,
        session: AsyncSession,
    ) -> datetime:
        """По списку слотов и дате возвращает время начала бронирования."""
        slots_ids = [table_slot['slot_id'] for table_slot in tables_slots]
        slots = await slot_crud.get_by_list_of_id(
            session=session,
            sequence_id=slots_ids,
        )
        booking_time = min(
            [slot.start_time for slot in slots],
        )
        return datetime.combine(booking_date, booking_time)

    async def delete_multi(
        self,
        session: AsyncSession,
        objs: list[BookingDish],
    ) -> None:
        """Удаляет несколько объектов."""
        await session.execute(
            delete(BookingDish).where(
                BookingDish.id.in_(obj.id for obj in objs),
            ),
        )


class BookingTableSlotCRUD(CRUDBase):
    """CRUD операции для слотов бронирования."""

    async def is_available(
        self,
        slots: list[dict[str, int]],
        date: date,
        session: AsyncSession,
    ) -> bool:
        """Проверяет доступность запрошенных слотов."""
        conditions = []
        for slot in slots:
            conditions.append(
                and_(
                    BookingTableSlot.table_id == slot.get('table_id'),
                    BookingTableSlot.slot_id == slot.get('slot_id'),
                    BookingTableSlot.is_active,
                    BookingTableSlot.booking.has(
                        and_(
                            Booking.status.in_(
                                (BookingStatus.BOOKING, BookingStatus.ACTIVE),
                            ),
                            Booking.booking_date == date,
                        ),
                    ),
                ),
            )

        stmt = select(BookingTableSlot).where(or_(*conditions))
        result = await session.execute(stmt)
        if result.scalar():
            return False
        return True

    async def get_by_id_list_bts(
        self,
        session: AsyncSession,
        cafe_id: int,
        model: type[Slot | Table],
        id_list: Optional[list[int]] = None,
    ) -> list[Slot | Table]:
        """Получает список объектов по их идентификаторам."""
        if id_list is None or len(id_list) == 0:
            raise ValueError(Constants.ID_LIST_NEEDED)
        stmt = select(model).where(
            model.id.in_(id_list),
            model.cafe_id == cafe_id,
            model.is_active,
        )
        query = await session.execute(stmt)
        return list(query.scalars().all())

    async def delete_multi(
        self,
        session: AsyncSession,
        objs: list[BookingTableSlot],
    ) -> None:
        """Удаляет несколько объектов."""
        await session.execute(
            delete(BookingTableSlot).where(
                BookingTableSlot.id.in_(obj.id for obj in objs),
            ),
        )

    async def get_capacity(
        self,
        session: AsyncSession,
        tables_slots: list[dict[str, int]],
    ) -> int:
        """Получает вместимость бронирования."""
        tables_ids = [slot['table_id'] for slot in tables_slots]
        tables = await table_crud.get_by_list_of_id(session, tables_ids)
        return sum(table.seat_number for table in tables)


booking_crud = BookingCRUD(Booking)
booking_table_slot_crud = BookingTableSlotCRUD(BookingTableSlot)
