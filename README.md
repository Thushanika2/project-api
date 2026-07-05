# Conference Scheduler API

Flask REST API for the Conference Scheduler full-stack project.

## Requirements

- Python 3.12+
- MySQL 8+

## Setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

2. Create the MySQL database:

```sql
CREATE DATABASE conf_scheduler CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. Copy `.env.example` to `.env` and fill in your database credentials:

```
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_NAME=conf_scheduler
JWT_SECRET_KEY=change-me-to-a-long-random-string
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=1440
FLASK_DEBUG=1
```

4. Seed demo data:

```bash
python seed.py
```

5. Run the development server:

```bash
python run.py
```

The API listens on `http://127.0.0.1:5000`.

## Production (Railway)

- Set the same environment variables in Railway.
- Start command: `gunicorn run:app --bind 0.0.0.0:$PORT`

## Demo Accounts

| Role      | Email                     | Password |
| --------- | ------------------------- | -------- |
| Organizer | organizer@confsched.test  | Admin123 |
| Attendee  | alice@confsched.test      | Alice123 |
| Attendee  | bob@confsched.test        | Bob123   |

## API Overview

- `POST /api/auth/register` — register (defaults to attendee)
- `POST /api/auth/login` — login, returns JWT
- `GET /api/sessions` — public schedule (filter by track, speaker, time)
- `GET /api/agenda` — attendee personal agenda
- `POST /api/agenda` — add session (capacity check + clash warning)
- Organizer CRUD for tracks and sessions with CSV/PDF import/export
