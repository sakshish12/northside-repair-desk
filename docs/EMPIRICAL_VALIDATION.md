# Empirical validation (portfolio evidence)

Professor feedback asked for **runtime proof**, not only design diagrams. This folder is generated from the real test suite and load script.

## How to reproduce

```bash
cd northside-booking/backend
source .venv/bin/activate   # or: python3 -m venv .venv && pip install -r requirements.txt
python scripts/generate_evidence.py
```

Outputs (committed after you run locally, or downloaded from **GitHub Actions** artifacts):

| File | Contents |
|------|----------|
| `evidence/pytest_output.txt` | Full `pytest -v` log |
| `evidence/load_test_output.txt` | 20 parallel POSTs: status counts, p95 latency, DB row count |
| `evidence/README.md` | Run timestamp and exit codes |

## What to cite in Phase 3

1. **Concurrency:** Excerpt from `pytest_output.txt` showing `test_parallel_bookings_single_winner` passed.
2. **Database state:** Excerpt from `load_test_output.txt` line `CONFIRMED rows for this slot in DB: 1`.
3. **Idempotency:** `test_idempotency_same_client_request_id` and `test_parallel_same_client_request_id_one_row`.
4. **Edge cases:** `test_edge_cases.py` (cancelled rows, invalid interval, UTC storage, 409 leaves one row).
5. **CI:** Screenshot or link to green GitHub Actions run (workflow `.github/workflows/ci.yml`).

## Load test interpretation

The load script is **not** a benchmark paper. It supports an honest sentence such as:

> Under 20 simultaneous booking attempts for one slot, the API returned one success and nineteen conflicts, with a single confirmed row in SQLite.

See `backend/scripts/load_test_booking.py` for parameters.
