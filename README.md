# MovieLog - дневник фильмов

Учебный проект по УП.05 «Проектирование и разработка информационных систем».
Автор: Закиров Радель Рустемович.

MovieLog - веб-приложение, где пользователь ведёт дневник просмотренных фильмов:
добавляет фильмы из каталога, ставит оценки, пишет отзывы и получает подборку
фильмов под настроение с помощью ИИ.

## Технологии
- Python 3.12, Django
- PostgreSQL 16
- HTML5, CSS3, JavaScript
- Git, GitHub

## Роли
- **Пользователь** - ведёт свой дневник, ставит оценки, получает подборки ИИ.
- **Администратор** - ведёт каталог фильмов и жанров, управляет пользователями.

## Запуск
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # указать пароль от PostgreSQL
createdb movielog_db
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Структура
- `accounts/` - пользователи и токены восстановления пароля
- `diary/` - фильмы, жанры, записи дневника, подборки ИИ
- `db/schema.sql` - SQL-скрипт структуры базы
- `docs/diagrams/` - UML-диаграммы и ERD (draw.io)
