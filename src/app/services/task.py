def get_reminder_id(booking_id: int) -> str:
    """Генерирует уникальный ID задачи на основе ID брони."""
    return f"reminder-booking-{booking_id}"
