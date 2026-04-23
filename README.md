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
docker compose exec app alembic revision --autogenerate -m "Add UserModel"
docker compose exec app alembic upgrade head
```

При создании первого пользователя ему автоматически назначается роль Администратора.


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

!Обратите внимание на создание volume pgdata для БД в папке infra.

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
