# ClimateShield

AI-powered parametric climate risk and insurance platform for smallholder farmers.

**Hack for Impact 2026 — KCT** · Theme: *AI for Climate Resilience*

```bash
make install && make db-up && make migrate && make seed-demo && make dev
# API + interactive docs: http://localhost:8000/docs
```

> **Status: backend foundation in place; risk engine and frontend not started.**
> [`docs/10`](./docs/10-implementation-status.md) is the as-built record ·
> [`docs/`](./docs/README.md) is the approved plan ·
> [`backend/README.md`](./backend/README.md) explains how to run it.

## The idea

A farmer registers a farm with a map pin, a crop, and a sowing date. ClimateShield prices the
weather risk for that location, issues a policy whose payout rule is a machine-readable contract,
and evaluates it daily against cached weather. When rainfall crosses the threshold, payout is
automatic — no claim, no surveyor, no discretion.

Traditional crop insurance cannot serve a 1.2-hectare plot: the loss assessment costs more than the
crop. Parametric insurance pays on a *measurement* instead of an *inspection*, which is what makes
the economics work at this scale.

## Two properties that shape the whole system

**No AI component authorises a payout.** Trigger evaluation is pure arithmetic over stored inputs —
identical today and in ten years. An import-graph test fails the build if anyone adds a model, a
network client, or a data-access import to that path. AI prices risk and explains outcomes; it never
produces them.

**Nothing on the read path touches the network.** Weather providers are *ingestion* sources writing
into a local cache; evaluation reads only from that cache. That makes a settled policy reproducible
from stored data alone, and it means the demo runs with the network unplugged.

## Stack

Next.js 15 · TypeScript · Tailwind · Leaflet *(not started)* — FastAPI · Python 3.11 · SQLAlchemy ·
Alembic — PostgreSQL 16, PostGIS optional — pandas · scikit-learn · LightGBM *(not started)* —
Open-Meteo (ERA5) with committed offline fixtures as the default provider — Claude *(not started)*

## Licence

MIT — see [LICENSE](./LICENSE).
