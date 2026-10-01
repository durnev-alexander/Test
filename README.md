# Приложение ЖКХ

Веб-приложение для диспетчеризации ЖКХ. Стек: React + TypeScript + Vite, FastAPI, PostgreSQL, Docker Compose.

## Возможности первого прототипа
- Авторизация через backend (демо-учётная запись для разработки: `demo` / `demo`).
- Защищённая рабочая область диспетчера.
- Начальная структура справочника адресов.
- PostgreSQL и запуск через Docker Compose.

> Внимание: `demo/demo` предназначено только для локальной разработки. Перед развёртыванием замените секреты и отключите демо-пользователя.

## Запуск
1. Установите Docker Desktop / Docker Engine с Compose.
2. Скопируйте `.env.example` в `.env`.
3. Выполните `docker compose up --build`.
4. Откройте http://localhost:8080.

API документация: http://localhost:8000/docs

## Структура
- `frontend/` — React + TypeScript + Vite.
- `backend/` — FastAPI, SQLAlchemy и JWT.
- `database/` — начальная схема PostgreSQL.
- `docker-compose.yml` — локальный стек.

## Проверки
- Frontend: `npm run build`
- Backend: `pytest`
