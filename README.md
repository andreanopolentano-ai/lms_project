# LMS Project

Django REST Framework проект для LMS-системы.

## Реализовано

- Кастомная модель пользователя с авторизацией по email.
- Поля пользователя: phone, city, avatar.
- Модель Course.
- Модель Lesson.
- Связь Lesson с Course через ForeignKey.
- CRUD для Course через ViewSet.
- CRUD для Lesson через Generic-классы.
- Сериализаторы для Course, Lesson и User.
- Эндпоинт для просмотра и редактирования профиля пользователя.
- Подключен Django REST Framework.
- Подключены media-файлы.

## Проверки

- `python manage.py check`
- `python manage.py makemigrations --check`
- CRUD курсов проверен через DRF-интерфейс.
- CRUD уроков проверен через DRF-интерфейс.

## Запуск проекта через Docker Compose

### Требования

- Docker Desktop
- Docker Compose

### Подготовка переменных окружения

Создайте файл `.env` на основе примера:

```bash
cp .env.example .env
