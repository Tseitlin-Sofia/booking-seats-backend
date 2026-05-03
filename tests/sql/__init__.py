from pathlib import Path
from typing import Dict


class SQLQueries:
    """Контейнер для SQL запросов из файлов.

    Загружает SQL запросы из .sql файлов и кэширует их для повторного
    использования. Доступ к запросам осуществляется через свойства.
    """

    def __init__(self) -> None:
        """Инициализирует SQLQueries.

        Создает пустой кэш запросов и определяет путь к директории,
        где хранятся .sql файлы (текущая директория файла).
        """
        self._queries: Dict[str, str] = {}
        self._sql_dir = Path(__file__).parent

    def _load(self, name: str) -> str:
        """Загружает SQL запрос из файла.

        - Args:
            name: Имя файла без расширения .sql

        - Returns:
            Содержимое SQL файла в виде строки

        - Raises:
            FileNotFoundError: Если файл с указанным именем не существует
            UnicodeDecodeError: Если файл не в кодировке UTF-8

        """
        if name not in self._queries:
            file_path = self._sql_dir / f'{name}.sql'
            self._queries[name] = file_path.read_text(encoding='utf-8')
        return self._queries[name]

    @property
    def create_test_schema(self) -> str:
        """Создает тестовую схему и копирует структуру таблиц."""
        return self._load('create_test_schema')

    @property
    def clean_test_schema(self) -> str:
        """Очищает данные в тестовой схеме (TRUNCATE)."""
        return self._load('clean_test_schema')

    @property
    def drop_test_schema(self) -> str:
        """Полностью удаляет тестовую схему."""
        return self._load('drop_test_schema')

    @property
    def check_schema_exists(self) -> str:
        """Проверяет существование схемы."""
        return self._load('check_schema_exists')

    @property
    def count_tables_in_schema(self) -> str:
        """Подсчитывает количество таблиц в схеме."""
        return self._load('count_tables_in_schema')

    @property
    def check_tables_exist(self) -> str:
        """Проверяет наличие таблиц в test схеме."""
        return self._load('check_tables_exist')

    @property
    def set_search_path(self) -> str:
        """Устанавливает search_path для сессии."""
        return self._load('set_search_path')

    @property
    def reset_search_path(self) -> str:
        """Сбрасывает search_path к public."""
        return self._load('reset_search_path')


sql = SQLQueries()
