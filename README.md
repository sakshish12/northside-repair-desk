# Northside Repair Desk

Fictional single-site appointment scheduling demo for **DLMCSPCSP01** (Sakshi Sharma, 4243437). The API rejects overlapping **CONFIRMED** bookings on the same repair bench using **SQLite `BEGIN IMMEDIATE`** transactions and a shared half-open interval overlap predicate.

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, Vite, TypeScript |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2 |
| Database | SQLite (file `backend/northside.db`) |
| Tests | pytest, httpx (parallel booking simulation) |

## Quick start

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Seed demo data (also runs from the UI on load):

```bash
curl -X POST http://127.0.0.1:8000/admin/seed
```

API docs: http://127.0.0.1:8000/docs

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open http://127.0.0.1:5173

### Tests

```bash
cd backend
source .venv/bin/activate
pytest -v
```

The concurrency test fires **10 parallel** `POST /appointments` for the same slot and asserts **1×201**, **9×409**, and **one** confirmed row in the database.

### Portfolio evidence (Phase 3)

```bash
cd backend
source .venv/bin/activate
python scripts/generate_evidence.py
```

Writes `docs/evidence/pytest_output.txt` and `load_test_output.txt` for the report. See `docs/EMPIRICAL_VALIDATION.md` and `docs/SQLITE_CONCURRENCY.md`.

CI runs the same tests on push (`.github/workflows/ci.yml`).

### Reminder job (mock)

```bash
cd backend
source .venv/bin/activate
python -m app.jobs.reminders
```

Logs due appointments within the next 24 hours (`MAIL_MODE=log`).

## Design notes

- **Server authority**: overlap checks run in `BookingService`, not in React.
- **Intervals**: UTC storage, half-open `[start, end)` — touching slots do not overlap.
- **Cancel**: soft delete via `CANCELLED` status; freed slots are bookable again.
- **Idempotency**: optional `client_request_id` on create (safe duplicate submits).

## Project layout

```
northside-booking/
├── README.md
├── backend/
│   ├── app/
│   │   ├── api/          # REST routes
│   │   ├── services/     # BookingService, overlap, seed
│   │   ├── models/
│   │   └── jobs/         # reminder worker
│   └── tests/
└── frontend/
    └── src/
```
