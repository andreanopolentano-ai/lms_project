# LMS Project

Учебный проект LMS на Django REST Framework. В проекте реализованы курсы, уроки, пользователи, подписки, платежи Stripe, документация API, фоновые задачи Celery и CI/CD.

## Основные возможности

- CRUD курсов и уроков;
- JWT-аутентификация;
- права владельца и модератора;
- пагинация, фильтрация и валидация ссылок;
- подписки на обновления курсов;
- PostgreSQL и Redis;
- Celery worker и Celery beat;
- документация OpenAPI через drf-spectacular;
- создание Stripe Product, Price и Checkout Session;
- сохранение Stripe ID и ссылки на оплату;
- синхронизация статуса платежа;
- Docker Compose, Gunicorn и Nginx;
- GitHub Actions: Tests → Lint → Build → Deploy.

## Документация API

После запуска проекта доступны:

- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`
- Health check: `http://127.0.0.1:8000/health/`

## Локальный запуск через Docker Compose

1. Создать `.env`:

```bash
cp .env.example .env
```

2. Заполнить обязательные значения в `.env`.

3. Запустить проект:

```bash
docker compose up --build -d
```

4. Проверить контейнеры:

```bash
docker compose ps
```

5. Остановить проект:

```bash
docker compose down
```

## Локальный запуск через Poetry

```bash
poetry install --with dev
poetry run python manage.py migrate
poetry run python manage.py runserver
```

Проверки:

```bash
poetry run python manage.py check
poetry run python manage.py makemigrations --check --dry-run
poetry run python manage.py test
poetry run ruff check . --exclude .venv,.idea,migrations
```

## Stripe

В `.env` необходимо задать тестовый ключ:

```env
STRIPE_API_KEY=sk_test_...
```

Основные маршруты:

- `POST /api/payments/create/` — создать продукт, цену и сессию оплаты;
- `GET /api/payments/` — список платежей текущего пользователя;
- `GET /api/payments/<id>/status/` — получить статус Stripe и синхронизировать локальную модель.

Стоимость передаётся в Stripe в копейках. Данные Stripe хранятся в полях `stripe_product_id`, `stripe_price_id`, `stripe_session_id`, `payment_url`, `payment_status` и `session_status`.

## CI/CD

Workflow `.github/workflows/ci-cd.yml` запускается при push в:

- `feature/ci-cd-deployment`;
- `develop`.

Этапы:

1. `Tests` — Django checks, проверка миграций и тесты;
2. `Lint` — Ruff;
3. `Build` — сборка образа и публикация в Docker Hub;
4. `Deploy` — обновление приложения и проверка версии через `/health/`.

### GitHub Actions secrets

Обязательные секреты:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `SERVER_IP`

Для прямого SSH-деплоя используются уже созданные секреты:

- `SSH_PORT`
- `SSH_USER`
- `SSH_PRIVATE_KEY`
- `DEPLOY_DIR`
- `ENV_FILE`

Если GitHub-hosted runner не может открыть входящее SSH-соединение, контейнер `auto_deploy` на сервере сам забирает новый образ из Docker Hub. Этап `Deploy` подтверждает, что сервер запустил образ с текущим `GITHUB_SHA`.

## Однократная подготовка сервера

На Windows из корня проекта выполните:

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\bootstrap_server.ps1
```

Скрипт:

- использует существующий локальный SSH-ключ;
- подключается к `deploy@72.56.232.208` через порт `2222`;
- отправляет Compose, Nginx и локальный `.env`;
- запускает контейнеры;
- запускает контейнер `auto_deploy`, который проверяет обновления каждые 5 минут.

После этого каждый новый образ `fapepa/lms-project:latest` автоматически применяется на сервере.

## Проверка production

```text
http://72.56.232.208/
http://72.56.232.208/api/docs/
http://72.56.232.208/health/
```

Успешный health-check содержит текущую версию образа:

```json
{
  "status": "ok",
  "version": "<git-commit-sha>"
}
```
