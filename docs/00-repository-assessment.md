# 00 — Current Repository Assessment

Assessment performed by inspecting every tracked and untracked file, full Git history, branch
topology, and the runtime environment.

## 1. What physically exists

The repository is a **bare GitHub scaffold**. Three files, 241 lines, one commit. There is no
application code of any kind.

```
climate-shield/
├── .gitignore   218 lines — GitHub's standard Python template, verbatim
├── LICENSE       21 lines — MIT, "Copyright (c) 2026 Akhilesh Selvan S"
└── README.md      2 lines — title + one-sentence description
```

| File | Content | Verdict |
|------|---------|---------|
| `README.md` | `# climate-shield` + *"AI-powered parametric climate risk and insurance platform for smallholder farmers."* | Placeholder. Needs full rewrite at H24. |
| `LICENSE` | Unmodified MIT, 2026, Akhilesh Selvan S | **Keep as-is.** Correct choice; permissive licence helps judging and reuse. |
| `.gitignore` | GitHub `Python.gitignore` template, unmodified — covers venv, `__pycache__`, pytest, mypy, ruff, Streamlit, Celery, Redis | **Usable but incomplete.** Has zero Node.js coverage. |

### `.gitignore` gap — first thing to fix

The template is Python-only. A polyglot repo will start committing junk within the first hour.
Missing entries that must be added in the very first implementation commit:

```
node_modules/       .next/          out/            dist/
.vercel/            .turbo/         *.tsbuildinfo
.env.local          .env*.local     .DS_Store
coverage/           playwright-report/
```

Note the template *does* already ignore `.env` — good, but not `.env.local`, which is exactly what
Next.js uses. This is a real credential-leak path and is a one-line fix.

## 2. Git state

| Property | Value |
|----------|-------|
| Remote | `https://github.com/AkhileshSelvan/climate-shield` |
| Commits | 1 — `f1ffb8c` *"Initial commit"*, 2026-08-17 19:10 IST |
| Author | Akhilesh Selvan S |
| Local branches | `main`, `claude/climateshield-architecture-plan-tphoz7` (current) |
| Remote branches | `origin/main`, `origin/claude/climateshield-architecture-plan-tphoz7` |
| Divergence | **Zero.** The working branch is identical to `main`. |
| Working tree | Clean |
| Tags / releases | None |

**Reading:** this is hour zero. Nothing is committed that constrains us, and there is no history to
work around. Every architectural decision is still free — which is precisely why they should be
made deliberately now rather than at 3am.

## 3. What is missing (complete inventory)

Everything below is absent and must be created:

**Application**
- [ ] Frontend application (no `package.json`, no framework, no UI)
- [ ] Backend service (no Python package, no `pyproject.toml`/`requirements.txt`, no entrypoint)
- [ ] Database schema, migrations, seed data
- [ ] Weather data ingestion + cache
- [ ] Risk / pricing engine
- [ ] Parametric trigger evaluation engine
- [ ] Payout ledger and disbursement simulation
- [ ] Authentication and authorization

**Engineering scaffolding**
- [ ] `docker-compose.yml` (Postgres + API for local parity)
- [ ] Dependency manifests and lockfiles
- [ ] Environment variable contract (`.env.example`)
- [ ] Test setup (pytest, Vitest)
- [ ] CI workflow (`.github/workflows/`)
- [ ] Linting/formatting config (ruff, eslint, prettier)
- [ ] `Makefile` / task runner for one-command dev startup

**Collaboration**
- [ ] `CONTRIBUTING.md`, branch protection, `CODEOWNERS`
- [ ] PR / issue templates
- [ ] Architecture documentation ← *this directory closes this gap*

**Product**
- [ ] Crop calendar reference data (phase definitions per crop)
- [ ] Insurance product definitions and trigger templates
- [ ] Demo seed dataset
- [ ] Pitch deck, demo script, backup recording

## 4. Runtime environment observed

Verified in this session's container. Relevant because it determines what can be validated here
versus what must be validated on team laptops.

| Capability | State | Consequence |
|-----------|-------|-------------|
| Node.js 22.22.2 / npm 10.9.7 | ✅ Available | Next.js 15 is safe to target |
| Python 3.11.15 | ✅ Available | FastAPI + modern typing fine |
| PostgreSQL 16 **client** (`psql`) | ⚠️ Client only, **no server running** | Need Docker locally or a hosted DB |
| Docker CLI 29.3.1 | ⚠️ CLI present, **daemon not running** | `docker-compose` cannot be validated *in this session*; works on laptops |
| `pandas`, `scikit-learn`, `fastapi`, `geopandas` | ❌ Not installed | Clean slate; nothing pre-pinned |
| PyPI / npm registry | ✅ Reachable (proxy bypass list) | Dependency installation works |
| `api.open-meteo.com` | ❌ **HTTP 403 at egress proxy** | See below |
| `archive-api.open-meteo.com` | ❌ **HTTP 403 at egress proxy** | See below |
| `power.larc.nasa.gov` | ❌ **HTTP 403 at egress proxy** | See below |

### The weather-API finding matters

All three candidate weather sources are blocked by this session's organization egress policy
(confirmed via the proxy status endpoint: `connect_rejected — gateway answered 403 to CONNECT`).
This is a restriction of *this cloud session*, not of the team's own machines.

Two consequences, both of which the architecture already wants anyway:

1. **Live weather integration must be built and verified on a team laptop**, or the host must be
   added to the egress allowlist for this environment. It cannot be smoke-tested from here.
2. **It validates the cache-first design.** The system must treat the weather API as a *batch
   ingestion source*, never as a synchronous dependency of a request. Every read path serves from
   the `weather_observation` table. This was already the right call for auditability — a parametric
   contract must settle against a stored, versioned dataset, not a live call whose response nobody
   kept. The network restriction just makes it non-negotiable.

## 5. Assessment summary

| Dimension | Status |
|-----------|--------|
| Existing code to preserve | **None** — greenfield |
| Existing code to refactor | **None** |
| Technical debt inherited | **None** |
| Blocking constraints | **None** |
| Immediate fixes needed | `.gitignore` Node coverage; README rewrite |
| Risk from the blank slate | **Scope drift.** With nothing built, everything feels possible. Sections 02 and 08 exist to counter this. |

The most valuable property of this repository right now is that it is empty. The plan that follows
should be treated as the constraint that the emptiness lacks.
