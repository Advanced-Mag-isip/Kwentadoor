# Kwentadoor

## Tech Stack
| Layer    | Technology |
|----------|-----------|
| Backend  | Django + Django REST Framework |
| Frontend | Next.js (TypeScript + Tailwind CSS) |
| Database | PostgreSQL |


## Initial Project Structure

```bash
Kwentadoor/
├── backend/
│   ├── accounting_core/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   ├── payroll/
│   │   ├── migrations/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── expenses/
│   │   ├── migrations/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── analytics/
│   │   ├── migrations/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── audit/
│   │   ├── migrations/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── venv/
│   ├── manage.py
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── src/
    │   └── app/
    │       ├── favicon.ico
    │       ├── globals.css
    │       ├── layout.tsx
    │       └── page.tsx
    ├── public/
    ├── .env.local
    ├── next.config.ts
    ├── package.json
    ├── tailwind.config.ts
    └── tsconfig.json
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

## Initial Setup

### 1. Clone the repository

```bash
git clone https://github.com/Advanced-Mag-isip/Kwentadoor.git
cd Kwentadoor
```

### 2. Set up the PostgreSQL database

```bash
psql -U postgres
```

```sql
CREATE USER your_user WITH PASSWORD 'yourpassword';
CREATE DATABASE your_db OWNER your_user;
GRANT ALL PRIVILEGES ON DATABASE your_db TO your_user;
\q
```

### 3. Set up the backend

```bash
cd backend

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file inside `backend/`:

```env
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432

DTR_API_BASE_URL=
DTR_API_KEY=your-dtr-api-key
```

To generate a secret key:

```bash
python -c "import secrets; print(secrets.token_hex(50))"
```

Run migrations and create an admin account:

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Set up the frontend

```bash
cd ../frontend
npm install
```

Create a `.env.local` file inside `frontend/`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Running the Project

Open two terminals:

```bash
# Terminal 1 — backend
cd backend
venv\Scripts\activate       # Windows
python manage.py runserver
```

```bash
# Terminal 2 — frontend
cd frontend
npm run dev
```