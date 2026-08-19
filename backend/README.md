# ClimateShield Backend

FastAPI + SQLAlchemy. Parametric climate-risk insurance for smallholder farmers.

## Quickstart (fresh machine, no network needed)

```bash
make install          # create .venv, install backend/requirements.txt
make db-up            # start local PostgreSQL via docker compose
cp backend/.env.example backend/.env
make migrate          # apply Alembic migrations
make seed-demo        # load weather fixtures + demo farm and policy
make dev              # http://localhost:8000/docs
```

No Docker? Set `DATABASE_URL=sqlite:///./climateshield.db` in `backend/.env`.
SQLite is supported for tests and quick local runs; **PostgreSQL is the
deployment target.**

### Virtualenv location

`make install` creates the virtualenv at **`.venv` in the repository root**, and every
`make` target uses it. If you already have one somewhere else, point make at it rather
than recreating it:

```bash
make VENV=backend/venv test
```

Any target that needs the virtualenv checks for it first and tells you what to run,
so a missing or differently-named venv fails with a clear message instead of
`No such file or directory`.

### Running uvicorn directly

`make dev` runs uvicorn from inside `backend/`, and that working directory is what
puts `app` on the import path. The raw command from the repository root fails with
`ModuleNotFoundError: No module named 'app'`, so run it from `backend/`:

```bash
cd backend && ../.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

## The one thing to understand

**Trigger evaluation never touches the network.** Weather providers are
*ingestion* sources that write into the `weather_observations` cache; evaluation
reads only from that cache. This makes a settled policy reproducible from stored
data alone — and it means the whole demo runs with the network unplugged.

```
OpenMeteoProvider ─┐
NasaPower (later) ─┼─▶ POST /weather/ingest ─▶ weather_observations ─▶ evaluation ─▶ payout
FixtureProvider ───┘        (only networked path)         (cache)        (deterministic)
     ▲ default
```

`WEATHER_PROVIDER=fixture` is the default in development, test and demo, so the
offline path is the one that gets exercised.

## Guarantees under test

| Guarantee | Test |
|-----------|------|
| A double-click never produces two payouts | `tests/test_idempotency.py` |
| Money is exact Decimal, never float | `tests/test_money.py` |
| The happy path runs with sockets blocked | `tests/test_weather_offline.py` |
| Simulation is deterministic and repeatable | `tests/test_idempotency.py` |
| No AI/network import on the money path | `tests/test_architecture.py` |

`make test`

## API

Canonical paths are under `/api/v1`; the original unprefixed paths still work
(hidden from the schema) so in-flight work keeps running. Interactive docs at
`/docs`.

| Method | Path | Notes |
|--------|------|-------|
| `GET` | `/health` | Reports active provider and database engine |
| `POST` `GET` | `/api/v1/farms/` | Snaps to a weather grid cell on create |
| `POST` | `/api/v1/weather/ingest` | **Only** endpoint that may reach a network |
| `GET` | `/api/v1/weather/{farm_id}` | Cached weather |
| `POST` `GET` | `/api/v1/policies/` | Money accepted and returned as decimal strings |
| `POST` | `/api/v1/triggers/check/{policy_id}` | Idempotent per policy per date |
| `POST` | `/api/v1/simulate/drought/{policy_id}` | Demo lever, same code path as settlement |
| `POST` | `/api/v1/simulate/reset/{policy_id}` | Repeat a rehearsal |
| `GET` | `/api/v1/payouts/` | Read-only — no endpoint creates a payout |

## Migrations

```bash
cd backend && ../.venv/bin/python -m alembic revision --autogenerate -m "message"
cd backend && ../.venv/bin/python -m alembic upgrade head
```

If you have a `climateshield.db` from before the baseline migration, delete it —
the schema changed (weather cache, uniqueness constraints, decimal money).
