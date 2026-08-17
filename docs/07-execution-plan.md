# 07 — Git Strategy, Team Split & 30-Hour Execution

## 1. Git branching strategy

**Trunk-based development with short-lived feature branches.** Not GitFlow — a `develop` branch adds
a merge hop that nobody has time for, and release branches are meaningless when the release is a
laptop on a stage.

```
main ──●──────●──────●──────●──────●──────●──── (always demo-able)
        \    /  \   /  \   /  \   /  \   /
         ●──●    ●─●    ●─●    ●─●    ●─●
      feat/…  feat/…  feat/…  feat/…  hotfix/…
       < 4h    < 4h    < 4h    < 4h
```

### Rules

| Rule | Detail | Why |
|------|--------|-----|
| `main` is always demo-able | If `main` is broken, that is the only priority for whoever broke it | The demo can be needed at any hour |
| Branches live **< 4 hours** | Merge or abandon | Long branches are how 4 people produce 4 incompatible systems |
| Branches stay **< 400 lines** | Split larger work | Reviewable in 5 minutes at 3am |
| Naming | `feat/<area>-<slug>`, `fix/…`, `chore/…`, `hotfix/…` — e.g. `feat/risk-burn-analysis` | Area prefix shows ownership at a glance |
| Commits | Conventional Commits: `feat(risk): add climate-trend weighting` | Judges do browse the history |
| Merge | **Squash merge only** | Linear `main`, one revert per feature |
| Review | 1 approval before H24; self-merge permitted after H24 if CI is green | Review must not become the bottleneck at hour 25 |
| Never | `--force` on `main`; committing `.env`; committing generated API clients by hand | |

### Conflict avoidance is structural, not procedural

The directory layout in [01 §4](./01-architecture.md#4-repository-layout-proposed) is drawn so each
developer owns directories the others do not touch. `CODEOWNERS` encodes it:

```
/backend/app/models/      @dev-a
/backend/app/core/        @dev-a
/backend/alembic/         @dev-a
/backend/app/services/    @dev-b
/frontend/app/(farmer)/   @dev-c
/frontend/components/map/ @dev-c
/frontend/app/(admin)/    @dev-d
/frontend/components/ui/  @dev-d
/backend/app/schemas/     @dev-a @dev-b   # shared — change only via PR, announce in channel
```

`backend/app/schemas/` is the one genuinely shared surface, which is exactly why it is written first
and changed carefully.

### Integration checkpoints

Every 6 hours, **everyone merges to `main`**, the smoke test runs, and the build is tagged.

| Tag | Hour | Gate — must be true to proceed |
|-----|------|--------------------------------|
| `checkpoint-1` | H6 | Login works; a farm can be created and read |
| `checkpoint-2` | H12 | Farm → **real risk score** from real cached weather |
| `checkpoint-3` | H16 | Policy issued; trigger engine evaluates it |
| `checkpoint-4` | H20 | **Full happy path end to end**, locally |
| `checkpoint-5` | H24 | Deployed, seeded, first full rehearsal passed |
| **`demo-freeze`** | **H26** | **Feature work stops. `hotfix/*` only.** |

> **The H26 freeze is the most important line in this document.** The common hackathon failure is
> not running out of code — it is arriving at the pitch with untested code and an unrehearsed demo.
> Four hours of rehearsal and polish beats four hours of features, every time.

## 2. Four-person work split

Boundaries are drawn to **minimise shared files**, not to equalise line counts.

### Dev A — Platform & API Core
**Owns:** `backend/app/{core,models,api/v1}`, `alembic/`, `docker-compose.yml`, deployment, CI

- Repo scaffold, `.gitignore` Node entries, `Makefile`, CI workflow
- Full schema + Alembic migrations ([03](./03-data-model.md))
- Auth: OTP flow, JWT, role dependencies
- CRUD: farms, plantings, crops, products
- Policy issuance with trigger freezing
- Deployment: Supabase, Render, Vercel wiring; `.env.example`

**Critical path:** the schema and the auth stub must land by **H4** — three people are blocked
until they do. Dev A ships the migration before touching anything else.

### Dev B — Risk, Trigger & Payout Engine
**Owns:** `backend/app/services/{weather,risk,trigger,payout}`, `backend/app/jobs/`

- Open-Meteo client; 35-year backfill for 4 districts; grid-cell snapping
- Phase-wise index computation (cumulative rainfall, CDD, heat degree-days)
- **Burn analysis engine** + premium calculation ([05](./05-ai-ml-design.md))
- **Deterministic trigger evaluator** — idempotent, audited, unit-tested
- Payout state machine + ledger
- `/admin/simulate/weather` — the demo lever
- Monte Carlo, analogue-year early warning, LightGBM threshold optimisation (SHOULDs)

**Highest-risk workstream.** Starts the weather backfill at **H2** — it is the long pole and
everything downstream needs the cache populated. Owns the only unit tests that are mandatory
(index-window arithmetic).

### Dev C — Farmer Frontend
**Owns:** `frontend/app/{(auth),(farmer)}`, `frontend/components/map/`

- App shell, routing, auth screens, session handling
- **Map-based farm registration** (Leaflet) — the demo's first visual moment
- Crop and sowing-date entry
- Risk assessment view
- Quote → policy purchase flow
- **Monitoring dashboard** — season tracker against threshold
- Alerts feed, payout view, audit view
- Mobile-responsive throughout (it is presented as a farmer's phone)

Works against the **generated API client** from hour 3, with MSW mocks until endpoints land. Never
blocked waiting for Dev A.

### Dev D — AI/Risk Visualisation, Admin Simulation, Demo Systems & Documentation
**Owns:** `frontend/app/(admin)`, `frontend/components/{ui,charts}`, `frontend/messages/`,
`backend/app/services/explain/`, `backend/seeds/{demo,explanations}/`, `docs/`

**This is a full technical workstream.** Dev D writes backend and frontend code throughout, and
owns some of the most demo-critical software in the repository.

**Backend**
- **Claude explanation service** — prompt construction, structured-payload contract, response
  validation (rejects any number not present in the input), caching, static per-band fallbacks
- **Async generation pipeline** so explanation never blocks a risk response
- **Demo seed builders** — `make seed-demo`, the pre-warmed assessment, pre-generated explanations
- Contributes the demo half of the fixture system with Dev B (M14)

**Frontend**
- **Design system:** shadcn setup, tokens, light/dark — done early, unblocks Dev C
- **Risk visualisation:** 35-year trigger-years chart, season rainfall tracker vs threshold,
  forecast band, analogue-year projection display, portfolio exposure view. *This is how the risk
  engine becomes legible — the charts are the argument that the model is real.*
- **Admin simulation console** — the on-stage control surface for M9
- **i18n:** Tamil/English catalogues, toggle, locale-aware number and date formatting

**Documentation & demo systems**
- Keeps `docs/` current as decisions change; records approved scope amendments
- `README.md` rewrite at H24, architecture diagram, screenshots
- Demo script maintenance, rehearsal coordination, backup recording, statistic verification

> Dev D is a developer, not a presenter who also codes. The demo-systems work — simulation console,
> seed builders, pre-generated explanations, reset tooling — is engineering, and it is what makes
> the 4:30 script executable at all. Documentation sits here because the person who builds the admin
> console and the charts has the clearest view of how the whole system fits together.
>
> **Presenting is a separate decision made at H26**, and it goes to whoever is most rested and most
> fluent — which may well be someone else.

### Shared responsibilities
Everyone: seeds their own domain's fixtures, writes their own `.env.example` entries, keeps `main`
green, and updates the schema contract via PR with an announcement.

## 3. 30-hour execution sequence

Assumes a **09:00 Friday** start. Adjust offsets to the actual schedule; keep the *shape*.

### H0 – H2 · Foundation *(all four together, in one room)*
The highest-leverage two hours of the entire event.

- [ ] Scope frozen against [02](./02-mvp-scope.md). MUST list **and NON-GOALS** agreed out loud.
- [ ] **Open-Meteo connectivity verified from all four laptops** — see the gate below
- [ ] Repo scaffold: backend package, frontend app, `docker-compose.yml`, `Makefile`, CI
- [ ] `.gitignore` Node entries added; `.env.example` created
- [ ] **Pydantic schemas + OpenAPI contract written and merged** ← the unblocking artifact
- [ ] `WeatherProvider` protocol + `FixtureProvider` stub committed (M14 skeleton)
- [ ] `tests/test_architecture.py` committed and wired into CI (M15) — **it passes trivially now,
      which is exactly when to add it**
- [ ] Supabase project created; connection string shared. **Do not enable PostGIS.**
- [ ] `make dev` works on all four laptops — *verified, not assumed*
- [ ] Branch protection, `CODEOWNERS`, checkpoint tags agreed

#### Gate 1 — weather connectivity (must complete before H2)

Every developer runs, on their own machine and network:

```bash
curl -sS -o /dev/null -w "%{http_code}\n" \
  "https://archive-api.open-meteo.com/v1/archive?latitude=11.0&longitude=76.96\
&start_date=2024-06-01&end_date=2024-06-05&daily=precipitation_sum&timezone=auto"
```

| Result | Action |
|--------|--------|
| `200` on ≥ 1 laptop | That laptop becomes the **fixture-generation machine**. Dev B fetches all 35 years for 4 districts there and **commits the JSON immediately** — before writing any other code. |
| `200` on none | Retry on a phone hotspot. Still failing → switch to synthetic fixtures from published regional normals, labelled `"synthetic": true`. Decide by **H4**, not H8. |
| Works now, fails at the venue | Irrelevant — fixtures are committed and `FixtureProvider` is the default. |

**This gate exists because the assumption has already failed once:** all three weather hosts return
403 from the cloud session used to write this plan. Verify before depending on it.

**Exit gate:** four people can run the stack and generate a typed client; connectivity is a known
quantity rather than an assumption. Do not proceed otherwise.

### H2 – H6 · Parallel foundations
| Dev | Work |
|-----|------|
| A | Schema + migrations + auth (OTP, JWT, roles) — **must land by H4** |
| B | Open-Meteo client; **start the 35-year backfill** (long-running); grid-cell snapping |
| C | App shell, auth screens, map component with mock data |
| D | Design system, chart components against mock data, i18n scaffold |

**`checkpoint-1` at H6:** login works, a farm can be created and read.

### H6 – H12 · Core domain
| Dev | Work |
|-----|------|
| A | Farms, plantings, crops, products endpoints; reference seeds |
| B | Phase-wise index computation; **burn analysis**; `POST /risk/assess`; **finish M14 fixture system** |
| C | Farm registration wired to the real API; risk view |
| D | Risk charts on real assessment data; Claude explanation service; demo seed builders |

**`checkpoint-2` at H12 — two gates, both hard:**
1. Register a farm → receive a **real** risk score from real cached weather. This is the moment the
   project becomes real.
2. **`make demo-offline` runs the stack with the network interface disabled**, and farm registration
   through risk assessment completes in that state (M14 acceptance, first pass).

If either slips, cut SHOULDs immediately. The offline gate is checked at H12 rather than H24
precisely so that the fallback is exercised for eighteen hours before it is needed.

### H12 – H16 · Insurance mechanics
| Dev | Work |
|-----|------|
| A | Quote + policy issuance with trigger freezing; deploy to staging |
| B | **Trigger evaluator**; scheduler; idempotency; index-window unit tests |
| C | Policy purchase flow; monitoring dashboard |
| D | Admin simulation console; Tamil catalogue |

**`checkpoint-3` at H16:** a policy can be issued and evaluated.

### H16 – H20 · Payouts, alerts, sleep rotation
> **Sleep is scheduled, not accidental.** Two developers sleep H16–H20, two sleep H20–H24. Four
> exhausted people at hour 28 is a worse outcome than four rested people with one fewer feature.
> The pair that stays awake takes low-conflict work.

| Dev | Work |
|-----|------|
| A | Payout endpoints; alerts; production deploy |
| B | Payout state machine; ledger; **`/admin/simulate/weather`**; early-warning projection |
| C | Alerts feed; payout view; audit view |
| D | Portfolio view; **start the pitch deck** |

**`checkpoint-4` at H20:** full happy path — register → assess → buy → monitor → simulate → trigger
→ payout — works locally.

### H20 – H24 · Integration & first rehearsal
- [ ] Everything deployed to public URLs
- [ ] Demo data seeded; **Claude explanations pre-generated and committed**
- [ ] `make demo-reset` working and verified repeatable **twice in a row**
- [ ] **M14 full acceptance:** the *complete* happy path — registration → assessment → policy →
      monitor → simulate → trigger → payout → audit — runs with the **network interface disabled**
- [ ] **Rehearsal #1, timed, end to end** — expect breakage; this is what the rehearsal is for
- [ ] Fix what broke; re-run

**`checkpoint-5` at H24.**

### H24 – H26 · Polish & freeze
- [ ] Loading states, empty states, error states
- [ ] Mobile responsive verified on a real phone
- [ ] Tamil strings reviewed by a Tamil speaker on the team
- [ ] `README.md` rewritten: problem, architecture diagram, screenshots, run instructions
- [ ] **Statistics verified and sourced** ([06](./06-demo-script.md#sources-to-verify-before-pitching))
- [ ] **Backup video recorded**
- [ ] **`demo-freeze` tag. Feature work stops.**

### H26 – H29 · Rehearse
- [ ] Rehearsal #2 and #3, timed, under 4:30
- [ ] Full offline run — **network disconnected**
- [ ] Deck finalised; presenter chosen; Q&A drilled from [06](./06-demo-script.md#judge-qa--prepared-answers)
- [ ] Only demo-blocking bugs fixed, on `hotfix/*`

### H29 – H30 · Buffer
Submission, final run-through, and deliberate stopping. **Nothing new is written in this hour.**

## 4. Definition of Done

A feature is done when: it is merged to `main`; the happy path was manually verified; it degrades
gracefully when its dependency is unavailable; it appears in the demo script **or** is explicitly
marked out-of-demo; and it does not break `make demo-reset`.

## 5. Communication cadence

- **Stand-up every 6 hours** at each checkpoint. Three questions: what merged, what is blocked,
  what is at risk. Ten minutes, standing.
- **Blocked > 30 minutes → say so immediately.** Silent blockage is the most expensive failure mode
  available to a four-person team on a clock.
- **`main` broken → announce in channel and fix before anything else.**
- One channel. No DMs for project decisions — decisions made in DMs get re-litigated at hour 27.
