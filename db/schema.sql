-- База данных веб-приложения MovieLog (дневник фильмов)
-- Автор: Закиров Р. Р.
-- Основной способ создания структуры - миграции Django (python manage.py migrate).
-- Этот скрипт показывает ту же структуру в виде SQL.

CREATE DATABASE movielog_db WITH ENCODING 'UTF8' TEMPLATE template0;
\c movielog_db

-- 1. Пользователи
CREATE TABLE users (
    id           BIGSERIAL    PRIMARY KEY,
    username     VARCHAR(150) NOT NULL UNIQUE,
    email        VARCHAR(150) NOT NULL UNIQUE,
    password     VARCHAR(128) NOT NULL,              -- хеш пароля (PBKDF2)
    role         VARCHAR(20)  NOT NULL DEFAULT 'user'
                 CHECK (role IN ('user', 'admin')),
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- 2. Жанры
CREATE TABLE genres (
    id    BIGSERIAL   PRIMARY KEY,
    name  VARCHAR(50) NOT NULL UNIQUE
);

-- 3. Фильмы (общий каталог)
CREATE TABLE movies (
    id           BIGSERIAL    PRIMARY KEY,
    title        VARCHAR(200) NOT NULL,
    year         SMALLINT     NOT NULL CHECK (year BETWEEN 1888 AND 2100),
    description  TEXT,
    poster_url   VARCHAR(300),
    created_by   BIGINT       REFERENCES users(id) ON DELETE SET NULL,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- 4. Связь фильмов и жанров (многие ко многим)
CREATE TABLE movie_genres (
    movie_id  BIGINT NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    genre_id  BIGINT NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
    PRIMARY KEY (movie_id, genre_id)
);

-- 5. Записи дневника
CREATE TABLE diary_entries (
    id          BIGSERIAL   PRIMARY KEY,
    user_id     BIGINT      NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
    movie_id    BIGINT      NOT NULL REFERENCES movies(id) ON DELETE RESTRICT,
    status      VARCHAR(20) NOT NULL DEFAULT 'want'
                CHECK (status IN ('want', 'watched')),
    rating      SMALLINT    CHECK (rating BETWEEN 1 AND 10),
    review      TEXT,
    watched_at  DATE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, movie_id)
);

-- 6. Подборки ИИ
CREATE TABLE ai_recommendations (
    id             BIGSERIAL    PRIMARY KEY,
    user_id        BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mood           VARCHAR(100) NOT NULL,
    request_text   TEXT,
    response_text  TEXT         NOT NULL,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- 7. Токены восстановления пароля
CREATE TABLE password_reset_token (
    id          BIGSERIAL   PRIMARY KEY,
    user_id     BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  CHAR(64)    NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Индексы по внешним ключам
CREATE INDEX idx_movies_created_by  ON movies(created_by);
CREATE INDEX idx_diary_user_id      ON diary_entries(user_id);
CREATE INDEX idx_diary_movie_id     ON diary_entries(movie_id);
CREATE INDEX idx_ai_user_id         ON ai_recommendations(user_id);
CREATE INDEX idx_prt_user_id        ON password_reset_token(user_id);
CREATE INDEX idx_prt_expires        ON password_reset_token(expires_at);
