"""CRUD операции для бронирования."""

from datetime import date
from typing import Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import BookingConstants as Constants
from app.core.logging import get_logger
from app.crud.base import CRUDBase
from app.models import (
    Booking,
    BookingDish,
    BookingTableSlot,
    Dish,
    Slot,
    Table,
)
from app.schemas.booking import BookingStatus
from app.schemas.booking import BookingTableSlot as BookingTableSlotSchema
from app.schemas.dish import PreOrderItemCreate

logger = get_logger()


class BookingCRUD(CRUDBase):
    """CRUD операции для бронирования."""

    async def get_bookings(
        self,
        session: AsyncSession,
        show_active: Optional[bool] = True,
        cafe_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> list[Booking]:
        """Получает бронирования."""
        stmt = select(Booking).options(
            selectinload(
                Booking.tables_slots,
            ),
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


class BookingTableSlotCRUD(CRUDBase):
    """CRUD операции для слотов бронирования."""

    async def is_available(
        self,
        slots: list[BookingTableSlotSchema],
        date: date,
        session: AsyncSession,
    ) -> bool:
        """Проверяет доступность запрошенных слотов."""
        # for slot in slots:
        #     stmt = (
        #         select(BookingTableSlot)
        #         .where(
        #             BookingTableSlot.table_id == slot.table_id,
        #             BookingTableSlot.slot_id == slot.slot_id,
        #             BookingTableSlot.is_active,
        #             BookingTableSlot.booking.has(
        #                 and_(
        #                     Booking.status.in_((
        #                         BookingStatus.BOOKING,
        #                         BookingStatus.ACTIVE,
        #                     )),
        #                     Booking.booking_date == date,
        #                 ),
        #             ),
        #         )
        #         .exists()
        #     )
        #             result = await session.execute(select(stmt))
        # if result.scalar():
        #     logger.warning(
        #         Constants.SLOT_ALREADY_BOOKED.format(
        #             slot.slot_id,
        #             slot.table_id,
        #         ),
        #     )
        #     return False
        conditions = []
        for slot in slots:
            conditions.append(
                and_(
                    BookingTableSlot.table_id == slot.table_id,
                    BookingTableSlot.slot_id == slot.slot_id,
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

    async def get_by_id_list(
        self,
        session: AsyncSession,
        cafe_id: int,
        model: type[Slot | Table],
        id_list: Optional[list[int]] = None,
    ) -> list[Slot | Table]:
        """Получает список объектов по их идентификаторам."""
        if id_list is None:
            raise ValueError(Constants.ID_LIST_NEEDED)
        stmt = select(model).where(
            model.id.in_(id_list),
            model.cafe_id == cafe_id,
            model.is_active,
        )
        query = await session.execute(stmt)
        result = list(query.scalars().all())
        if len(result) != len(id_list):
            raise ValueError(Constants.TABLE_OR_SLOT_ERROR)
        return result


booking_crud = BookingCRUD(Booking)
booking_table_slot_crud = BookingTableSlotCRUD(BookingTableSlot)
