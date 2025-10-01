
# BAS-analytics-MVP

Простой MVP для аналитики: PostGIS + FastAPI + React. Можно быстро поднять локально, загружать файлы и смотреть базовые метрики по регионам.

---

## Содержание

1. О проекте
2. Что нужно для запуска
3. Быстрый старт с Docker
4. Локальный запуск backend
5. Локальный запуск frontend
6. Настройки и переменные окружения
7. Загрузка данных
8. Полезные API эндпоинты
9. Импорт данных и проверка job
10. Если работаешь с большими файлами
11. Логи и отладка
12. Очистка репозитория от больших файлов
13. Советы для продакшна
14. requirements.txt

---

## 1. О проекте

Это MVP аналитической платформы.

* Backend на FastAPI, база PostGIS.
* Frontend на React, показывает дашборд и метрики.
* Есть возможность загружать файлы и импортировать их в базу.

---

## 2. Что нужно для запуска

* Docker Desktop с WSL2 (Windows)
* Python 3.10+ (для локального запуска backend)
* Node.js + npm (для frontend)
* PowerShell

---

## 3. Быстрый старт с Docker

В корне репозитория:

```powershell
docker compose up -d --build
docker compose ps        # проверить, что всё поднялось
docker compose logs -f api
```

* Backend будет доступен по `http://localhost:8000`.
* Health-check: `http://localhost:8000/health`

---

## 4. Локальный запуск backend

Если хочешь запускать Python напрямую:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

---

## 5. Локальный запуск frontend

```powershell
cd frontend
npm install
npm start
```

* Dev сервер по умолчанию на `http://localhost:3000`.
* Можно указать proxy в `package.json`, чтобы фронтенд автоматически обращался к backend:

```json
"proxy": "http://localhost:8000"
```

---

## 6. Настройки и переменные окружения

В `docker-compose.yml` для сервиса api:

```yaml
environment:
  DATABASE_URL: "postgresql://postgres:postgres@db:5432/gis"
  ADMIN_TOKEN: "supersecret123"
  SECRET_KEY: "dev-secret-change-me"
  API_ALLOWED_ORIGINS: "http://localhost:3000,http://localhost:5173"
```

> Для продакшна меняем `ADMIN_TOKEN` и `SECRET_KEY`.

---

## 7. Загрузка данных

### 7.1. Через UI

1. Кладём файл в `./data`.
2. Загружаем через фронтенд на эндпоинт `/api/v1/upload`.
3. Запускаем импорт через `/api/v1/import_from_upload`.

### 7.2. Через curl / PowerShell

```powershell
curl.exe -X POST "http://localhost:8000/api/v1/upload" `
  -H "Authorization: Bearer supersecret123" `
  -F "file=@./data/parsed.ndjson"

curl.exe -X POST "http://localhost:8000/api/v1/import_from_upload" `
  -H "Authorization: Bearer supersecret123"
```

Импорт в фоне (job):

```powershell
curl.exe -X POST "http://localhost:8000/api/v1/import" `
  -H "Authorization: Bearer supersecret123" `
  -H "Content-Type: application/json" `
  -d "{\"file_url\":\"/data/uploaded_parsed.ndjson\"}"

curl.exe -X GET "http://localhost:8000/api/v1/job/1" `
  -H "Authorization: Bearer supersecret123"
```

---

## 8. Полезные API

* `GET /health` — проверка состояния сервера
* `GET /api/v1/flights` — список полётов
* `GET /api/v1/regions` — метрики по регионам
* `POST /api/v1/upload` — загрузка файла (только admin)
* `POST /api/v1/import_from_upload` — импорт загруженного файла (admin)
* `POST /api/v1/import` — фоновые задачи (admin)
* `GET /api/v1/job/{id}` — проверка статуса job

---

## 9. Импорт данных

* Если файл большой, используем `cur.copy_expert` из Python или `\COPY` через psql.
* Для маленьких файлов хватает `import_from_upload` — вставляет по батчам.
* Проверить импорт:

```powershell
docker compose exec db psql -U postgres -d gis -c "SELECT count(*) FROM staging_raw;"
```

---

## 10. Работа с большими файлами

1. Загружаем в `./data` или S3
2. Используем `psql \COPY` или Python batch insert
3. Запускаем `load_from_staging.sql`
4. Обновляем таблицы регионов

---

## 11. Логи и отладка

```powershell
docker compose logs -f api
docker compose logs -f db
docker compose exec api ls -l /data
docker compose exec db ls -l /data
```

---

## 12. Очистка репозитория

Большие файлы лучше не хранить в GitHub.

Добавляем в `.gitignore`:

```
/data/*.ndjson
/data/*.dump
/data/*.sql
*.dump
*.sql
node_modules/
.venv/
```

Удаляем из индекса:

```powershell
git rm --cached data/parsed.ndjson
git rm --cached data/parsed_normalized.ndjson
git commit -m "Remove big files from repo"
git push
```

---

## 13. Советы для продакшна

* Меняем токены и секретные ключи
* Для больших файлов используем S3 + Celery/Redis
* Фоновые воркеры для импорта
* Резервные копии базы и исходных файлов

---

## 14. requirements.txt

```
fastapi
uvicorn[standard]
pandas
openpyxl
psycopg2-binary
requests
matplotlib
pytest
python-multipart
```

