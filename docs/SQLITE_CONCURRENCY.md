# SQLite concurrency behaviour (Northside Repair Desk)

This document supports the Phase 3 portfolio discussion of database guarantees.

## Why SQLite for this project

SQLite fits a coursework monorepo: single file, no separate server, easy for markers to clone and run. It is **not** a substitute for a multi-tenant production calendar backed by PostgreSQL, but it is sufficient to demonstrate **application-level** concurrency control and to measure behaviour under parallel HTTP requests.

## Relevant SQLite properties

| Topic | Behaviour in this project |
|--------|---------------------------|
| Writers | At most **one** write transaction at a time per database file. |
| Readers | Multiple readers can proceed while no writer holds the lock. |
| Deferred `BEGIN` | A transaction may read until the first write, then request a lock; two writers can both pass a read-phase overlap check unless the lock is taken early. |
| `BEGIN IMMEDIATE` | Reserves a write lock at transaction start. Used in `BookingService._begin_immediate()` so overlap read + insert run under an exclusive writer lock. |
| `busy_timeout` | Set to 5000 ms on connect (`PRAGMA busy_timeout=5000`) so brief lock contention returns `SQLITE_BUSY` after waiting instead of failing instantly. |
| Foreign keys | `PRAGMA foreign_keys=ON` for referential integrity. |

## What the application guarantees

1. **Invariant:** No two `CONFIRMED` appointments on the same `resource_id` may have intersecting half-open intervals `[start, end)`.
2. **Mechanism:** Overlap predicate in Python + transactional create with `BEGIN IMMEDIATE` on SQLite.
3. **Conflict response:** HTTP **409** when a second *different* booking competes for the same slot.
4. **Idempotency:** Unique `client_request_id`; duplicate submits (retries or parallel tabs with the same key) return the **same** row instead of creating duplicates.

## What SQLite does *not* guarantee here

- **Serializable scheduling across multiple API processes** each with its own DB file (not our deployment model; one API, one file).
- **Declarative exclusion constraints** on time ranges (PostgreSQL `EXCLUDE USING gist` would add a second line of defence; we rely on service-layer checks + tests).
- **High write throughput** under dozens of simultaneous writers (SQLite serialises writes; the load script documents median/p95 latency honestly).

## Comparison with PostgreSQL (future work)

PostgreSQL would allow:

- Range exclusion constraints at the database layer.
- Higher concurrent write throughput with row-level locking.
- Clearer isolation level documentation for markers (`SERIALIZABLE`, etc.).

For Phase 3, the honest claim is: **correctness is enforced in `BookingService` and verified by automated parallel tests**, while SQLite provides a simple, auditable persistence layer with explicit `IMMEDIATE` transactions.

## Code references

- `app/core/database.py` — pragmas on connect.
- `app/services/booking.py` — `BEGIN IMMEDIATE`, overlap check, idempotency.
- `tests/test_booking_concurrency.py` — 10 parallel POSTs, 1×201 / 9×409.
- `tests/test_idempotency_parallel.py` — 10 parallel POSTs, same `client_request_id`, 1 DB row.
