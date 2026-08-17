# 07 — Git Strategy, Team Split & 30-Hour Execution

> **Authority (D3).** This document is canonical for **engineering execution and governance**:
> branching and PR workflow, CODEOWNERS, integration checkpoints and gates, team ownership,
> AI-tooling policy, communication cadence, and the engineering Definition of Done.
>
> It is **not** the hackathon schedule. Phases, wall-clock work blocks, the Golden Demo and
> submission preparation are owned by
> [`HACKATHON_EXECUTION_PLAN.md`](./HACKATHON_EXECUTION_PLAN.md).
> Product scope is owned by [`02-mvp-scope.md`](./02-mvp-scope.md).

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
# Backend + database + APIs                          -> issue #5
/backend/app/core/                @Bhagavathianu
/backend/app/models.py            @Bhagavathianu
/backend/app/api/                 @Bhagavathianu
/backend/alembic/                 @Bhagavathianu
/backend/requirements.txt         @Bhagavathianu
/docker-compose.yml               @Bhagavathianu

# Data, policy engine, fixtures, tests                -> issue #7
/backend/app/services/weather/    @Kirishwaran
/backend/app/services/trigger_engine.py  @Kirishwaran
/backend/app/services/payout_engine.py   @Kirishwaran
/backend/app/services/evaluation.py      @Kirishwaran
/backend/seeds/                   @Kirishwaran
/backend/tests/                   @Kirishwaran

# AI / risk engine + architecture                     -> issue #4
/backend/app/services/risk/       @AkhileshSelvan
/backend/app/services/explain/    @AkhileshSelvan
/docs/                            @AkhileshSelvan

# Frontend                                            -> issue #6
/frontend/                        @Karthik

# Shared contract — change by PR only, announce in channel
/backend/app/schemas.py           @Bhagavathianu @AkhileshSelvan
```

`backend/app/schemas.py` is the one genuinely shared surface — it is the contract Karthik's frontend
generates its client from — which is exactly why it changes by PR only and gets announced.

`backend/app/services/` is split by *concern*, not owned wholesale: Bhagavathianu owns the API and
persistence around it, Kirishwaran owns the policy/trigger/weather logic inside it, and Akhilesh owns
the risk and explanation modules when they land. That split follows the issue boundaries exactly.

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

**Ownership is defined by GitHub issues #4–#7, which are the source of truth.** The roles below
restate those issues in build order; where they differ, the issues win.

Boundaries are drawn to **minimise shared files**, not to equalise line counts. Nobody works outside
their boundary without coordinating first.

| Owner | Issue | Domain |
|-------|-------|--------|
| **Akhilesh** | [#4](https://github.com/AkhileshSelvan/climate-shield/issues/4) | Product owner · AI/ML · system architecture |
| **Bhagavathianu** | [#5](https://github.com/AkhileshSelvan/climate-shield/issues/5) | Backend · database · APIs |
| **Karthik** | [#6](https://github.com/AkhileshSelvan/climate-shield/issues/6) | Frontend · dashboard · UI/UX |
| **Kirishwaran** | [#7](https://github.com/AkhileshSelvan/climate-shield/issues/7) | Data/research · policy engine · testing · presentation |

Workflow for everyone: **issue checklist → feature branch → PR → review → merge.**

---

### Akhilesh — Product, AI/ML & Architecture · [#4](https://github.com/AkhileshSelvan/climate-shield/issues/4)
**Owns:** `backend/app/services/risk/`, `backend/app/services/explain/`, `docs/`

- **Tier-1 burn-analysis risk engine** — the mandatory risk component ([05](./05-ai-ml-design.md))
- Risk-score input/output contract, so Bhagavathianu can expose it and Karthik can render it
- Claude explanation layer (optional enhancement — must degrade to a static per-band string)
- MVP scope authority: **the only person who can approve work outside the agreed scope** ([02 §6](./02-mvp-scope.md#6-scope-discipline-rules))
- Architecture review on major PRs; cross-workstream integration
- Technical answers for judge Q&A ([06](./06-demo-script.md#judge-qa--prepared-answers))

**Working rule from #4:** keep AI out of the payout authorization path. Risk prediction informs the
product; deterministic trigger logic controls settlement. This is enforced by
`tests/test_architecture.py`, which fails the build on violation.

**Critical path:** the risk engine is the largest remaining gap between plan and code. Nothing else
blocks on it, which is exactly why it can slip unnoticed.

---

### Bhagavathianu — Backend, Database & APIs · [#5](https://github.com/AkhileshSelvan/climate-shield/issues/5)
**Owns:** `backend/app/{core,api}`, `models.py`, `alembic/`, `requirements.txt`, `docker-compose.yml`

- FastAPI application, routers, dependency wiring
- SQLAlchemy models and Alembic migrations ([03](./03-data-model.md))
- **Shared PostgreSQL** — stand up one instance the whole team points at
- Auth: OTP flow, JWT, role dependencies (not yet started)
- **Stable OpenAPI contract** — Karthik generates his typed client from it, so breaking changes get announced
- Deployment and environment configuration

> **Already delivered — do not re-implement.** PR #3 completes most of #5's checklist: the
> `WeatherProvider` abstraction with cache and fixture fallback, trigger/payout idempotency,
> `Float` → `Decimal(14,2)`, the move toward shared PostgreSQL, `requirements.txt`, and backend
> tests. The task on #5 is to **review and merge PR #3**, then continue with auth and the shared
> database instance. Re-writing that work would be the duplication #4 warns against.

---

### Karthik — Frontend, Dashboard & UI/UX · [#6](https://github.com/AkhileshSelvan/climate-shield/issues/6)
**Owns:** `frontend/` entirely

- Next.js foundation, design system, reusable components
- Farmer and farm registration flow (map pin, crop, sowing date)
- Climate-risk dashboard and risk visualisation
- Policy/coverage view, monitoring and alerts, payout/settlement status
- Integration against the OpenAPI contract — **generate the client, never hand-write it**
- Loading, empty, error and **offline/demo** states
- Responsive: it is presented as a farmer's phone

**Unblocked from now.** The backend contract is stable and documented at `/docs`, and every
endpoint works offline from fixtures — so the frontend can be built and demonstrated without
waiting on live weather or on the risk engine.

**Scope discipline:** the golden path only. Extra screens are the most common way a hackathon
frontend runs out of time.

---

### Kirishwaran — Data, Research, Policy Engine & Testing · [#7](https://github.com/AkhileshSelvan/climate-shield/issues/7)
**Owns:** `backend/app/services/{weather,trigger_engine,payout_engine,evaluation}`, `backend/seeds/`, `backend/tests/`

**This is a technical workstream.** Presentation is a secondary responsibility, not the role.

- **Weather data research** — evaluate sources, document the settlement-source argument
- **Prepare and validate the demo dataset**: run `make fixtures-live` to replace the current
  synthetic fixtures with real ERA5. **This is the single highest-priority task on the board.**
- Define transparent trigger rules — explicit units, windows and thresholds ([04](./04-api-design.md))
- Policy and trigger-engine logic, against Bhagavathianu's API contract
- **Test cases for trigger boundaries, crop windows and payout scenarios** — owns `backend/tests/`
- Validate the demo scenario and its audit evidence
- Research/evidence notes behind the pitch; **verify every statistic before it is spoken**
  ([06](./06-demo-script.md#sources-to-verify-before-pitching))
- Deck content, judge Q&A prep, end-to-end rehearsal including the offline fallback

**Why the engines sit here:** the trigger and payout engines are policy logic, not API plumbing.
Keeping them with the person who defines the rules and writes the tests puts the specification and
its verification in the same pair of hands.

---

### Shared responsibilities
Everyone: seeds their own domain's fixtures, keeps `main` green, works from their issue checklist,
and announces changes to `backend/app/schemas.py` before merging.

### AI tooling is a personal choice, not a team standard

**No developer is required to use any particular AI assistant.** Bhagavathianu, Karthik and
Kirishwaran each choose their own tools; nothing in this plan assumes otherwise, and no task should
ever be written so that it only works with a specific assistant. Akhilesh happens to work with
Claude and ChatGPT — that is his workflow, not a team requirement.

What *is* shared is the output contract, and it is tool-agnostic by design:

| Shared | Not shared |
|--------|-----------|
| The OpenAPI schema and generated client | How you write the code |
| Conventional Commits, branch and PR conventions | Which editor or assistant you use |
| Tests must pass; `main` stays green | Whether tests were hand-written or generated |
| Issue checklists #4–#7 | Your local setup |

> **Do not confuse the two senses of "Claude" in this repository.** The product calls the Claude API
> at runtime for vernacular explanation — a **Tier-4 optional enhancement** owned by Akhilesh (#4)
> and described in [05 §6](./05-ai-ml-design.md). That is a product dependency with a static
> fallback. It says nothing about how any teammate writes code.

### Where the workstreams touch

| Boundary | Rule |
|----------|------|
| Risk engine ↔ API | Akhilesh defines the contract in `schemas.py`; Bhagavathianu exposes it |
| Policy engine ↔ API | Kirishwaran owns the logic; Bhagavathianu owns the route that calls it |
| API ↔ Frontend | OpenAPI is the interface. Karthik generates; breaking changes get announced |
| Fixtures ↔ Demo | Kirishwaran owns both, so demo data and demo script cannot drift apart |
| Anything ↔ Scope | Only Akhilesh approves work outside the agreed MVP scope |

## 3. 30-hour execution sequence

**H0–H30 are relative engineering offsets, not the organizer's event clock.** H0 is whenever the
team begins building; the sequence describes order and dependency, not calendar time. The
authoritative wall-clock schedule — phases, session blocks, submission window — is
[`HACKATHON_EXECUTION_PLAN.md`](./HACKATHON_EXECUTION_PLAN.md), which remains subject to the
organizer's official timetable.

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
| `200` on ≥ 1 laptop | That laptop becomes the **fixture-generation machine**. Kirishwaran runs `make fixtures-live` there and **commits the JSON immediately**. |
| `200` on none | Retry on a phone hotspot. Still failing → switch to synthetic fixtures from published regional normals, labelled `"synthetic": true`. Decide by **H4**, not H8. |
| Works now, fails at the venue | Irrelevant — fixtures are committed and `FixtureProvider` is the default. |

**This gate exists because the assumption has already failed once:** all three weather hosts return
403 from the cloud session used to write this plan. Verify before depending on it.

**Exit gate:** four people can run the stack and generate a typed client; connectivity is a known
quantity rather than an assumption. Do not proceed otherwise.

### H2 – H6 · Parallel foundations
| Owner | Work |
|-------|------|
| Bhagavathianu | Schema + migrations + auth (OTP, JWT, roles) — **must land by H4** |
| Kirishwaran | Open-Meteo client; **start the 35-year backfill** (long-running); grid-cell snapping |
| Karthik | App shell, auth screens, map component with mock data |
| Akhilesh | Design system, chart components against mock data, i18n scaffold |

**`checkpoint-1` at H6:** login works, a farm can be created and read.

### H6 – H12 · Core domain
| Owner | Work |
|-------|------|
| Bhagavathianu | Farms, plantings, crops, products endpoints; reference seeds |
| Kirishwaran | Phase-wise index computation; **burn analysis**; `POST /risk/assess`; **finish M14 fixture system** |
| Karthik | Farm registration wired to the real API; risk view |
| Akhilesh | Risk charts on real assessment data; Claude explanation service; demo seed builders |

**`checkpoint-2` at H12 — two gates, both hard:**
1. Register a farm → receive a **real** risk score from real cached weather. This is the moment the
   project becomes real.
2. **`make demo-offline` runs the stack with the network interface disabled**, and farm registration
   through risk assessment completes in that state (M14 acceptance, first pass).

If either slips, cut SHOULDs immediately. The offline gate is checked at H12 rather than H24
precisely so that the fallback is exercised for eighteen hours before it is needed.

### H12 – H16 · Insurance mechanics
| Owner | Work |
|-------|------|
| Bhagavathianu | Quote + policy issuance with trigger freezing; deploy to staging |
| Kirishwaran | **Trigger evaluator**; scheduler; idempotency; index-window unit tests |
| Karthik | Policy purchase flow; monitoring dashboard |
| Akhilesh | Admin simulation console; Tamil catalogue |

**`checkpoint-3` at H16:** a policy can be issued and evaluated.

### H16 – H20 · Payouts, alerts, sleep rotation
> **Sleep is scheduled, not accidental.** Two developers sleep H16–H20, two sleep H20–H24. Four
> exhausted people at hour 28 is a worse outcome than four rested people with one fewer feature.
> The pair that stays awake takes low-conflict work.

| Owner | Work |
|-------|------|
| Bhagavathianu | Payout endpoints; alerts; production deploy |
| Kirishwaran | Payout state machine; ledger; **`/admin/simulate/weather`**; early-warning projection |
| Karthik | Alerts feed; payout view; audit view |
| Akhilesh | Portfolio view; **start the pitch deck** |

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

## 4. Engineering Definition of Done

A feature is done when: it is merged to `main`; the happy path was manually verified; it degrades
gracefully when its dependency is unavailable; it appears in the demo script **or** is explicitly
marked out-of-demo; and it does not break `make demo-reset`.

This is the *engineering* bar. Demo and submission readiness are defined in
[`HACKATHON_EXECUTION_PLAN.md`](./HACKATHON_EXECUTION_PLAN.md#definition-of-done).

## 5. Communication cadence

- **Stand-up every 6 hours** at each checkpoint. Three questions: what merged, what is blocked,
  what is at risk. Ten minutes, standing.
- **Blocked > 30 minutes → say so immediately.** Silent blockage is the most expensive failure mode
  available to a four-person team on a clock.
- **`main` broken → announce in channel and fix before anything else.**
- One channel. No DMs for project decisions — decisions made in DMs get re-litigated at hour 27.
