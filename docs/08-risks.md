# 08 — Technical Risks & Fallback Plans

Ordered by expected damage. Each risk names a **trigger condition** (how we know it is happening), a
**fallback** (what we do instead), and **when we decide** — because the expensive failure is not
having a fallback, it is deciding to use it too late.

---

### R1 · Weather API unavailable, rate-limited, or blocked — **severity: critical**

**Already confirmed as real:** all three candidate sources return HTTP 403 at this session's egress
proxy ([00 §4](./00-repository-assessment.md#the-weather-api-finding-matters)). Venue networks
routinely block or throttle outbound traffic too.

| | |
|---|---|
| **Primary control** | **Answered by a MUST-have feature, not a fallback.** M14 — the offline fixture system — makes `FixtureProvider` the *default* in dev, test, and demo. Committed 35-year JSON for 4 districts; the demo runs from Git alone. |
| **Gate** | **Gate 1 at H0–H2:** every developer curls the archive API from their own laptop. Whichever machine succeeds becomes the fixture-generation box, and the JSON is committed *before any other code is written*. |
| **Mitigation** | Cache-first architecture — weather is a batch ingestion source; no read path calls upstream |
| **Fallback 1** | NASA POWER as an independent secondary source, behind the same `WeatherProvider` interface |
| **Fallback 2** | Synthetic generator: fit a Gamma distribution to published regional normals, generate a 35-year series, **labelled `"synthetic": true` in the fixture header and in the UI.** We never present generated numbers as measurements. |
| **Decision point** | No laptop reaches the API by **H4** → switch to synthetic fixtures. Moved earlier from H8 because everything downstream depends on the cache. |
| **Verification** | **H12 first pass, H24 full pass:** the happy path runs with the network interface **disabled**. Not "should" — must, and it is a checkpoint gate. |

---

### R2 · Demo fails on stage — **severity: critical**

The one failure that cannot be recovered afterwards.

| | |
|---|---|
| **Mitigation** | Three timed rehearsals; `demo-freeze` at H26; `make demo-reset` between runs |
| **Fallback 1** | Local `docker-compose` stack, already running on `localhost`, seeded, warm |
| **Fallback 2** | A second policy pre-seeded in `triggered` state — if simulation fails, open it and continue narrating |
| **Fallback 3** | **Backup video recorded at H26**, on a phone and a USB stick |
| **Fallback 4** | Static screenshots in the deck as a final floor |
| **Decision point** | Any rehearsal failure that recurs twice → that step is scripted around, not debugged at hour 28 |

---

### R3 · ML model underperforms or has no usable training data — **severity: medium**

District-level yield data may be unavailable, stale, or too coarse to fit anything meaningful.

| | |
|---|---|
| **Mitigation** | **Tier 1 burn analysis needs zero training data and is built first.** The tiering in [05](./05-ai-ml-design.md) exists precisely for this. |
| **Fallback 1** | Ship Tiers 1–2 only. Burn analysis + Monte Carlo is a complete, defensible product. |
| **Fallback 2** | If Tier 3 held-out performance is poor, report it honestly as a limitation. **A stated limitation costs far less with technical judges than a silently overfitted model.** |
| **Decision point** | Tier 3 not producing sane cross-validated numbers by **H20** → drop it, no debate |

---

### R4 · Deployment fails or venue network blocks the hosted app — **severity: high**

| | |
|---|---|
| **Mitigation** | Deploy early (H16 staging, H20 production) rather than discovering it at H28 |
| **Fallback 1** | `docker-compose up` on the presenter's laptop, rehearsed |
| **Fallback 2** | Cloudflare Tunnel from the laptop if judges want to interact |
| **Fallback 3** | Phone hotspot |
| **Decision point** | Production not reachable by **H22** → local becomes the primary demo target and the deployed URL becomes the bonus |

---

### R5 · Merge conflicts and integration chaos — **severity: high**

Four developers, one repo, thirty hours, sleep deprivation.

| | |
|---|---|
| **Mitigation** | Contract-first at H0–H2; directory ownership via `CODEOWNERS`; < 4h branches; squash merges; 6-hourly checkpoints |
| **Fallback 1** | The schema owner (Dev A) resolves any conflict in `backend/app/schemas/` unilaterally |
| **Fallback 2** | If two people conflict repeatedly, one takes the file and the other works behind an interface |
| **Decision point** | `main` broken > 30 minutes → **everyone stops and fixes it** |

---

### R6 · PostGIS / geospatial setup consumes hours — **severity: low (designed out)**

Extensions, SRIDs, and GeoAlchemy types can silently eat an afternoon. **Ratified at sign-off: we do
not start there.**

| | |
|---|---|
| **Resolution** | **PostGIS is no longer the default — plain `latitude`/`longitude` `NUMERIC(9,6)` columns are.** This risk is designed out rather than managed. |
| **Why it works** | Grid snapping is `round(lat/0.1)*0.1`; district filtering is an indexed string; area is entered, not derived; distance, if ever needed, is Haversine in eight lines. **No MVP query performs a spatial operation.** |
| **Upgrade path** | If polygon boundaries or radius search become genuinely necessary: `CREATE EXTENSION postgis;` plus a migration adding `GEOGRAPHY(POINT,4326)` backfilled from the existing columns. Lat/lon remains the source of truth. |
| **Decision point** | Adopt PostGIS **only** if a MUST-have requires it *and* it costs under 30 minutes — never "while we're here, it might be useful later". |

---

### R7 · Auth becomes a rabbit hole — **severity: medium**

| | |
|---|---|
| **Mitigation** | Mock OTP (`123456`) from the start. No SMS gateway on the critical path, by design. |
| **Fallback 1** | Seeded demo users with a "log in as demo farmer" button |
| **Fallback 2** | Header-based dev auth (`X-Demo-User`) behind a `DEMO_MODE` flag |
| **Decision point** | Auth not working by **H6** → switch to the demo-login button; nothing downstream depends on real auth |

---

### R8 · Scope creep — **severity: high, probability: near-certain**

At 2am someone will propose blockchain settlement, IoT sensors, or a native app. It always happens.

| | |
|---|---|
| **Mitigation** | Explicit **NON-GOALS** list ([02 §5](./02-mvp-scope.md)) agreed aloud at kickoff, so refusing later is not a personal argument but a decision already made |
| **Rule** | **Nothing outside the agreed MUST / SHOULD / NICE lists gets built without explicit project-owner approval.** Anyone may propose; only the owner authorises. Ratified at sign-off. |
| **Rule** | Any addition must name **the feature it replaces** and who stops working on what |
| **Hard stop** | No new MUST after H8. No new anything after H26. |
| **Decision point** | If a MUST is at risk at H20, cut a SHOULD **immediately** — never compress rehearsal time |

---

### R9 · Date and timezone arithmetic produces silently wrong numbers — **severity: medium**

The most dangerous class of bug here, because it does not crash — it produces a plausible wrong
answer on stage, in front of people who understand crop calendars.

| | |
|---|---|
| **Mitigation** | All dates stored as UTC `DATE`. Windows expressed as **integer day offsets from `sowing_date`**, never as calendar dates. |
| **Mitigation** | Index-window arithmetic is the **one mandatory unit-test suite** (S9): boundary days, leap years, windows crossing a year end |
| **Fallback** | Hard-code the demo policy's window dates and verify the numbers by hand before the pitch |
| **Decision point** | Any discrepancy between UI and database index values → stop and fix before continuing feature work |

---

### R10 · LLM latency, quota, or refusal during the demo — **severity: low, visibility: high**

| | |
|---|---|
| **Mitigation** | Explanations generated **asynchronously** and **stored**; read paths never call the API |
| **Mitigation** | **Pre-generate every demo explanation before the pitch** |
| **Fallback** | Static per-risk-band strings in EN and TA. The UI must never render an error where an explanation belongs. |
| **Decision point** | Any generation failure during rehearsal → switch that entity to the static string permanently |

---

### R11 · Demo data drifts between rehearsals — **severity: medium**

Someone re-seeds, a number changes, and the narration no longer matches the screen.

| | |
|---|---|
| **Mitigation** | Deterministic seeds with fixed random seeds; `make demo-reset` as the single reset path |
| **Mitigation** | `is_simulated` flag makes injected weather removable without touching real data |
| **Fallback** | Database dump taken at H24 after a successful rehearsal; restore it before the pitch |
| **Decision point** | If the numbers in the script and the screen ever disagree, **the script is updated to match the system** — never the other way round |

---

### R12 · Team exhaustion — **severity: medium, underrated**

| | |
|---|---|
| **Mitigation** | **Scheduled sleep rotation** (H16–H20, H20–H24), not opportunistic napping |
| **Mitigation** | Feature freeze at H26 means the final four hours are low-cognitive-load work |
| **Fallback** | The most-rested person presents, regardless of who wrote the most code |
| **Rule** | **No architectural decisions after H24.** Tired teams rewrite things that already work. |

---

## Risk summary

| ID | Risk | Severity | Probability | Decide by |
|----|------|----------|-------------|-----------|
| R1 | Weather API unavailable | Critical → **controlled by M14** | **Confirmed** | **H4** |
| R2 | Demo fails on stage | Critical | Medium | H26 |
| R4 | Deployment fails | High | Medium | H22 |
| R5 | Integration chaos | High | Medium | continuous |
| R8 | Scope creep | High | **Near-certain** | H8 |
| R3 | ML underperforms | Medium | Medium | H20 |
| R6 | PostGIS overhead | **Designed out** | n/a | resolved |
| R7 | Auth rabbit hole | Medium | Low | H6 |
| R9 | Date arithmetic bugs | Medium | Medium | continuous |
| R11 | Demo data drift | Medium | Medium | H24 |
| R12 | Exhaustion | Medium | High | H16 |
| R10 | LLM failure | Low | Low | rehearsal |

**The three that decide the outcome:** R1 is already real, and at sign-off it was promoted from a
fallback plan to a MUST-have feature (M14) with an H12 gate — the strongest available answer. R8 is
near-certain and is answered by an agreement made at hour zero plus a named approver. R2 is answered
only by rehearsal time, which is why the H26 freeze is defended more strictly than any feature.

Two risks were **closed** at sign-off rather than mitigated: **R6**, by making PostGIS optional, and
the AI-in-the-money-path concern, by making the separation a build-failing test (**M15**). Designing
a risk out beats managing it.
