# Шаблон для проектов со стилизатором Ruff

## Основное

1. Базовая версия Python - 3.11.
2. В файле `requirements_style.txt` находятся зависимости для стилистики.
3. В каталоге `src` находится базовая структура проекта
4. В файле `srd/requirements.txt` прописываются базовые зависимости.
5. В каталоге `infra` находятся настроечные файлы проекта. Здесь же размещать файлы для docker compose.

## Запуск

Требуется запущенное приложение Docker.

```bash
cd infra
docker compose up [-d]
```

Для создания/применения миграций:
```bash
docker compose exec app alembic revision --autogenerate -m "description"
docker compose exec app alembic upgrade head
```

Для создания 1 суперпользователя:
Отправить POST запрос на users/ с валидными данными

Проверка создания таблиц:
```bash
docker compose exec db psql -U user -d db -c "\dt"
```

Доступ к приложени находится по адресу:
```
http://localhost:10000/
```

Проверка доступа (эндпойнты документации):
```
http://localhost:10000/redoc
http://localhost:10000/docs
```

## Структура проекта

Ниже представлено описание ключевых компонентов архитектуры приложения.

```bash
.
├── README.md                     # Документация проекта (текущий файл)
├── infra/                        # Инфраструктура и конфигурация для развертывания
│   ├── docker-compose.yml        # Оркестрация всех сервисов (app, nginx, БД, redis/celery)
│   ├── logs/                     # Хранилище логов, монтируемое в контейнеры
│   │   ├── app.2026-05-02_15-55-11_886740.log.zip # Архивы логов по датам
│   │   └── app.log               # Основной файл логов приложения
│   └── nginx/                    # Конфигурация веб-сервера (reverse-proxy)
│       ├── Dockerfile            # Сборка nginx с кастомной конфигурацией
│       └── nginx.conf            # Правила проксирования, статики, медиа
│
├── media/                        # Пользовательские загружаемые файлы (аватарки, фото блюд)
├── pytest.ini                    # Конфигурация тестового фреймворка pytest
├── requirements_style.txt        # Зависимости для линтинга и форматирования (ruff)
├── ruff.toml                     # Настройки линтера/форматтера ruff (аналог .flake8 + black)
│
├── src/                          # Исходный код приложения (ядро проекта)
│   ├── Dockerfile                # Сборка образа FastAPI приложения
│   ├── dockerignore              # Исключения для копирования в Docker-образ
│   ├── requirements.txt          # Основные Python-зависимости проекта
│   ├── celery_worker.py          # Точка входа для Celery worker (фоновые задачи)
│   ├── logs/                     # Локальные логи (могут быть переопределены в infra/)
│   │   └── app.2026-04-14_22-32-51_007836.log.zip
│   │
│   ├── alembic/                  # Миграции базы данных (управление схемой)
│   │   ├── README                # Документация Alembic
│   │   ├── env.py                # Скрипт окружения Alembic (подключение к БД)
│   │   ├── script.py.mako        # Шаблон для генерации новых миграций
│   │   └── versions/             # Файлы миграций (upgrade/downgrade)
│   │       └── ccbcb6ead64e_create_initial_migrations.py
│   ├── alembic.ini               # Конфигурация Alembic (пути, настройки подключения)
│   │
│   └── app/                      # Основной модуль приложения (FastAPI)
│       ├── __init__.py
│       ├── main.py               # Точка входа: создание FastAPI app, регистрация роутов, middleware
│       │
│       ├── api/                  # Слой API (контроллеры, валидация, маршруты)
│       │   ├── dependencies.py   # DI-зависимости (например, get_current_user, get_db)
│       │   ├── routers.py        # Объединение эндпоинтов в роутеры
│       │   ├── endpoints/        # Обработчики HTTP-запросов (ручки API)
│       │   │   ├── action.py     # Логирование действий пользователя
│       │   │   ├── auth.py       # Регистрация, логин, logout, сброс пароля
│       │   │   ├── booking.py    # Бронирование столиков
│       │   │   ├── cafe.py       # Управление кафе (CRUD)
│       │   │   ├── dish.py       # Блюда и меню
│       │   │   ├── media.py      # Загрузка/удаление изображений
│       │   │   ├── slot.py       # Временные слоты для бронирования
│       │   │   ├── table.py      # Столики в кафе
│       │   │   └── user.py       # Профиль пользователя, роли
│       │   └── validators/       # Бизнес-валидаторы на уровне API (повторное использование)
│       │       ├── action.py
│       │       ├── booking.py    # Проверка пересечений броней, доступности
│       │       ├── cafe.py
│       │       ├── dish.py
│       │       ├── media_validators.py  # Проверка типов/размеров файлов
│       │       ├── slot.py
│       │       ├── table.py
│       │       └── user.py
│       │
│       ├── celery/               # Фоновая обработка задач (Celery)
│       │   ├── celery_app.py     # Инициализация Celery, брокер (Redis/RabbitMQ)
│       │   └── tasks.py          # Асинхронные задачи (отправка писем, генерация отчетов)
│       │
│       ├── core/                 # Ядро приложения (конфиги, утилиты, middleware)
│       │   ├── base.py           # Базовые классы для моделей (BaseModel, TimestampMixin)
│       │   ├── config.py         # Pydantic-настройки (чтение из .env)
│       │   ├── constants.py      # Глобальные константы (роли, статусы, лимиты)
│       │   ├── db.py             # Подключение к БД (engine, sessionmaker)
│       │   ├── logging.py        # Настройка логгера (форматы, ротация)
│       │   ├── middleware.py     # Кастомные middleware (логирование, CORS, request_id)
│       │   └── user.py           # Утилиты работы с пользователем (хэширование, JWT)
│       │
│       ├── crud/                 # Слой работы с БД (CRUD операции)
│       │   ├── base.py           # Generic CRUD класс (наследуемый всеми)
│       │   ├── action.py         # Запись действий пользователя
│       │   ├── booking.py        # Создание/обновление броней
│       │   ├── cafe.py
│       │   ├── dish.py
│       │   ├── slot.py
│       │   ├── table.py
│       │   └── user.py
│       │
│       ├── models/               # SQLAlchemy ORM модели (таблицы в БД)
│       │   ├── action.py
│       │   ├── booking.py
│       │   ├── cafe.py
│       │   ├── dish.py
│       │   ├── slot.py
│       │   ├── table.py
│       │   └── user.py
│       │
│       ├── schemas/              # Pydantic схемы (валидация входящих/исходящих данных)
│       │   ├── action.py
│       │   ├── auth.py           # Схемы для логина, токенов, регистрации
│       │   ├── booking.py
│       │   ├── cafe.py
│       │   ├── dish.py
│       │   ├── slot.py
│       │   ├── table.py
│       │   ├── user.py
│       │   └── validators/       # Специфичные валидаторы внутри Pydantic-схем
│       │       ├── auth.py
│       │       └── booking.py
│       │
│       └── services/             # Бизнес-логика (слой сервисов)
│           ├── booking.py        # Логика бронирования (проверки, создание)
│           ├── media_service.py  # Работа с файлами (сохранение, удаление, ресайз)
│           ├── task.py           # Запуск Celery задач из API
│           └── user.py           # Регистрация, обновление профиля, права доступа
│
├── test.py                       # Возможно, скрипт для быстрого запуска тестов
│
└── tests/                        # Автотесты (pytest)
    ├── conftest.py               # Фикстуры для тестового окружения (клиент, сессия БД)
    ├── fixtures/                 # Переиспользуемые тестовые данные
    │   ├── auth.py               # Фикстуры с токенами, тестовыми пользователями
    │   ├── database.py           # Фикстуры для тестовой схемы PostgreSQL
    │   ├── logging.py            # Перехват логов в тестах
    │   └── payloads.py           # Шаблоны JSON-запросов
    ├── sql/                      # SQL-скрипты для управления тестовой БД
    │   ├── check_schema_exists.sql
    │   ├── check_tables_exist.sql
    │   ├── clean_test_schema.sql  # Очистка данных после тестов
    │   ├── count_tables_in_schema.sql
    │   ├── create_test_schema.sql  # Создание отдельной схемы для тестов
    │   ├── drop_test_schema.sql
    │   ├── reset_search_path.sql
    │   └── set_search_path.sql
    ├── test_logging.py           # Тесты логирования
    ├── test_middleware.py        # Тесты middleware (request_id, CORS)
    └── test_preorder.py          # Тесты логики предзаказа/бронирования
```

## Стилистика

Для стилизации кода используется пакеты `Ruff` и `Pre-commit`

Проверка стилистики кода осуществляется командой
```shell
ruff check
```

Если одновременно надо пофиксить то, что можно поиксить автоматически, то добавляем параметр `--fix`
```shell
ruff check --fix
```

Что бы стилистика автоматически проверялась и поправлялась при комитах надо добавить hook pre-commit к git

```shell
pre-commit install
```

## Требования к фронтенду.

При PATCH-запросе на эндпойнт `{server}/booking/{booking_id}` требуется ВСЕГДА передавать новый список BookingTableSlots.

## Авторы

[Яндекс.Практикум](https://github.com/yandex-praktikum)

[Максим Дацковский](https://github.com/NeSePeM) email: [<nspmax@ya.ru>](mailto:nspmax@ya.ru)
[Петрушенко Алексей](https://github.com/OnyxFireGlow) email:[<onyx.fireglow@gmail.com>](mailto:onyx.fireglow@gmail.com)
