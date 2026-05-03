from typing import TYPE_CHECKING, Any, Optional

from celery import Task

from app.core.logging import (
    get_logger,
    trace_id_ctx,
    user_id_ctx,
    username_ctx,
)

if TYPE_CHECKING:
    from celery.events import Event


class LoguruTask(Task):
    """Базовый класс для Celery задач с интеграцией loguru.

    Автоматически:
    1. Инициализирует контекст логирования
    2. Обрабатывает ошибки
    3. Логирует выполнение задач
    """

    _logger: Optional[Any] = None
    _logging_context: Optional[dict[str, str]] = None

    def __init__(self) -> None:
        """Инициализация задачи с настройкой логгера."""
        super().__init__()
        self._logger = get_logger()

    def _setup_logging_context(
        self,
        context: Optional[dict[str, str]] = None,
    ) -> None:
        """Восстанавливает контекст логирования если он передан.

        Args:
            context: Словарь с ключами 'trace_id', 'user_id', 'username'

        """
        if context:
            trace_id_ctx.set(context.get('trace_id', 'SYSTEM'))
            user_id_ctx.set(context.get('user_id', 'SYSTEM'))
            username_ctx.set(context.get('username', 'SYSTEM'))
        else:
            trace_id_ctx.set('CELERY')
            user_id_ctx.set('CELERY')
            username_ctx.set('CELERY')

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Перехватывает вызов задачи для установки контекста.

        Args:
            *args: Позиционные аргументы задачи
            **kwargs: Именованные аргументы задачи

        Returns:
            Any: Результат выполнения задачи

        """
        context = kwargs.pop('_logging_context', None)
        self._setup_logging_context(context)
        return super().__call__(*args, **kwargs)

    @property
    def log(self) -> Any:
        """Возвращает логгер с уже настроенным контекстом."""
        return self._logger

    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: list[Any],
        kwargs: dict[str, Any],
        einfo: Optional['Event'] = None,
    ) -> None:
        """Обработка ошибки с расширенным логированием.

        Args:
            exc: Исключение, вызвавшее ошибку
            task_id: Идентификатор задачи
            args: Позиционные аргументы задачи
            kwargs: Именованные аргументы задачи
            einfo: Информация об исключении

        """
        self.log.error(
            f'Задача {self.name}[{task_id}] завершилась с ошибкой: {exc}',
            exc_info=einfo,
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(
        self,
        exc: Exception,
        task_id: str,
        args: list[Any],
        kwargs: dict[str, Any],
        einfo: Optional['Event'] = None,
    ) -> None:
        """Логирование повторной попытки.

        Args:
            exc: Исключение, вызвавшее повторную попытку
            task_id: Идентификатор задачи
            args: Позиционные аргументы задачи
            kwargs: Именованные аргументы задачи
            einfo: Информация об исключении

        """
        self.log.warning(
            f'Задача {self.name}[{task_id}] будет повторена. Причина: {exc}',
            exc_info=einfo if einfo else None,
        )
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(
        self,
        retval: Any,
        task_id: str,
        args: list[Any],
        kwargs: dict[str, Any],
    ) -> None:
        """Логирование успешного выполнения.

        - Args:
            - retval: Результат выполнения задачи
            - task_id: Идентификатор задачи
            - args: Позиционные аргументы задачи
            - kwargs: Именованные аргументы задачи

        """
        self.log.info(f'Задача {self.name}[{task_id}] успешно выполнена')
        super().on_success(retval, task_id, args, kwargs)
