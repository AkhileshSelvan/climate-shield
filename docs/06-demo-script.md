# 06 — Demo Script (4 min 30 s + 30 s buffer)

## Setting

**Murugan**, a maize farmer with 1.2 ha of rainfed land in **Pollachi block, Coimbatore district,
Tamil Nadu** — roughly 50 km from the venue. Kharif 2026, sowing 15 June.

Local by design. A judging panel in Coimbatore recognises Pollachi, and a real place makes an
abstract product concrete in a way that "Farmer A in District X" never does.

## Pre-flight checklist — completed before walking on stage

- [ ] `make demo-reset` run; database in a known state
- [ ] All 35 years of weather cached for Coimbatore cells — **verified with the network disabled**
- [ ] Claude explanations pre-generated and stored for the demo assessment (EN + TA)
- [ ] Both browser tabs open and warm: farmer view, admin console
- [ ] Backup video (recorded at H26) open in a third tab
- [ ] Laptop on mains power, notifications silenced, screen at presentation resolution
- [ ] Phone hotspot ready — *and confirmed unnecessary*
- [ ] Run the full script once, end to end, immediately before the session

## Timed script

### 0:00 – 0:35 · The problem

> "Murugan farms 1.2 hectares of rainfed maize outside Pollachi. If the monsoon breaks during
> flowering, he loses the season. Crop insurance exists — but a claim needs a surveyor to visit and
> assess a one-hectare plot, and settlement typically takes months. On plots this small, the
> assessment costs more than the crop is worth. So most smallholders are, in practice, uninsured."

**On screen:** landing page. One statistic, large. *(Verify the exact figure and cite the source
before the pitch — see Sources below.)*

> "ClimateShield pays on a measurement, not an inspection."

---

### 0:35 – 1:15 · Onboarding and farm registration

Log in with a phone number, OTP `123456`. *(Say aloud: "mock OTP — a real gateway is one adapter
swap, and it isn't what you're here to judge.")*

Drop a pin on the map at Pollachi. Enter 1.2 ha. Select **Maize**, sowing date **15 June 2026**.

> "That's the entire input. A pin, a crop, a date. No paperwork, no land records, no surveyor."

**On screen:** map pin lands; the farm snaps to a weather grid cell, and the cell ID is visible.

> "Behind that pin, the farm is bound to an 11-kilometre reanalysis grid cell. Everything after this
> is computed against that cell — which is what makes it work for a 1.2 hectare plot."

---

### 1:15 – 2:20 · AI risk assessment · **first aha moment**

Click **Assess Risk**.

**On screen (< 3 s):**
- Trigger probability **23 %** · Risk band **MEDIUM** · Expected loss ratio **11.4 %**
- Bar chart: 35 seasons, 8 highlighted red — 1994, 2002, 2003, 2012, 2016, 2019, 2023, 2024
- Premium breakdown: pure ₹6,858 → gross ₹8,675 → after subsidy **farmer pays ₹2,169**

> "We just replayed thirty-five years of daily reanalysis weather for that exact grid cell. For each
> year we aligned the same crop calendar, measured rainfall across the flowering window — days 45 to
> 75 after sowing — and asked how often this contract would have paid. Eight times in thirty-five
> years. That's not a guess; it's a count. And because recent years are weighted more heavily, we're
> pricing the climate he's in, not the one his grandfather farmed."

Toggle to **தமிழ்**. Claude's explanation renders in Tamil.

> "Same numbers, farmer's language. Note what the model is doing here — translating and explaining.
> It is not producing the risk figure. Nothing an LLM generates touches a rupee in this system."

---

### 2:20 – 2:50 · The contract

**On screen:** the policy terms, in money and millimetres:

> **If rainfall between day 45 and day 75 after sowing falls below:**
> **120 mm → 25 % · 90 mm → 50 % · 60 mm → 100 % of ₹72,000**

> "Tiered, not all-or-nothing — 121 millimetres paying zero and 119 paying everything is how index
> insurance loses farmers' trust. And when Murugan accepts, this rule is *frozen onto his policy*.
> We can change the product tomorrow; his contract is what he agreed to today."

Click **Buy**. Policy `CS-2026-KH-000142` issued.

---

### 2:50 – 3:25 · Monitoring · **the resilience beat**

Open the policy dashboard. Season day 62. Flowering phase.

**On screen:** accumulated rainfall 71.2 mm tracking against the 120 mm threshold; 13 days left in
the window; 16-day forecast showing continued deficit.

An early-warning alert is already present:

> **⚠ 68 % chance your policy triggers within 12 days.**
> Of the 12 past seasons most similar to this one at day 62, 8 ended in a payout.
> Consider protective irrigation now.

> "This is the part I'd argue matters most. Insurance pays *after* the loss. This warns him *before*
> it — at day 62, with time to irrigate or adjust. That's climate resilience, not just compensation.
> And the method is transparent: we found the twelve historical seasons whose rainfall curve most
> resembles this one, and counted how they ended."

---

### 3:25 – 4:10 · The trigger · **second aha moment**

Switch to the admin console.

> "I'm going to compress a monsoon into ten seconds."

Select **Coimbatore · severe rainfall deficit · intensity 0.85**. Click **Simulate**, then
**Run evaluation now**.

**On screen, live:**
1. Weather cache updates for the affected cells
2. Evaluation runs — index resolves to **82.4 mm**
3. 82.4 < 90 → **tier 2 matched → payout 50 %**
4. Policy status → `triggered`
5. Payout **₹36,000** created → `pending` → `approved` → `disbursed`
6. Farmer view: SMS-style card — *"₹36,000 credited · UPI/CS/000142/01"*

**Point at the elapsed timer on screen.**

> "Trigger to money: **eleven seconds**. Industry benchmark for a settled crop-insurance claim is
> measured in months. No claim was filed. No surveyor was dispatched. Nobody exercised judgement."

---

### 4:10 – 4:30 · Audit and close

Open the evaluation record.

**On screen:** rainfall 82.4 mm · threshold 90 mm · window days 45–75 · 31 observations, 0 missing ·
source `open-meteo-era5` · engine `trigger-v1.0` · evaluated `2026-08-29T06:00:12Z`.

> "Every payout has this record. Exact measurements, the dataset, the engine version, the timestamp.
> Murugan can see precisely why he was paid — and so can a regulator, six months later. No adjuster,
> no dispute, no discretion. And the AI never touched the decision."

> "ClimateShield: a map pin to a priced, monitored, self-settling climate policy — in under five
> minutes."

---

## Judge Q&A — prepared answers

| Question | Answer |
|----------|--------|
| *"Is the AI real, or is it a wrapper?"* | The pricing engine is a 35-year historical replay with climate-trend weighting — that's the actuarial method reinsurers use. The threshold optimiser is a LightGBM model trained on district yield data. The LLM does explanation and translation only, deliberately, because a payout must be reproducible. |
| *"What about basis risk?"* | It's the central problem in index insurance, and we don't claim to eliminate it. We reduce it three ways: tiered rather than binary payouts, per-grid-cell rather than per-block pricing, and learned thresholds fitted to observed yield loss. We also measure and report it. |
| *"Why not blockchain?"* | The trust problem is "can I verify why I was paid." An append-only audit log with versioned inputs solves that. A chain would add a wallet, gas fees, and a failure mode without answering the question better. |
| *"Where does the money come from?"* | An insurer or reinsurer holds the risk; we're the pricing, monitoring, and settlement layer. Portfolio exposure and expected loss are in the admin view. Real deployment needs IRDAI filing and reinsurance capacity — we're not claiming otherwise. |
| *"How accurate is 11 km satellite data for 1.2 ha?"* | It can miss a single convective cell — that's a genuine limitation. Production would settle against a contractually agreed source such as IMD gridded data, calibrated against ground stations. We chose reanalysis because it's the only source with 35 years of consistent global coverage. |
| *"Can this scale?"* | The grid-cell design is the reason it can. A thousand farms in one block share one weather row per day. Cost per additional farmer is a database row and a hundred milliseconds of arithmetic — which is exactly why it works economically at 1.2 ha, where a surveyor never could. |
| *"What if the weather API is down?"* | Everything you just watched ran from the local cache. The API is a batch ingestion source, never a request-time dependency — for auditability first, and demo reliability second. |

## Failure recovery on stage

| If this fails | Do this |
|---------------|---------|
| Deployed URL unreachable | Switch to `localhost` — already running, already seeded |
| Simulation endpoint errors | Second pre-seeded policy is already `triggered`; open it and continue |
| Risk assessment slow | Pre-warmed assessment for the demo farm is cached; open it directly |
| Tamil explanation missing | Static fallback string renders — proceed without comment |
| Laptop or projector dies | Backup video, recorded at H26, on a phone and a USB stick |
| Running long at 3:00 | Cut the audit view; land the trigger and the eleven-second timer. **Never cut the trigger.** |

## Sources to verify before pitching

Every statistic spoken on stage must be checked and attributed. Do not present a number you cannot
source if asked.

- Smallholder share of Indian farm holdings — Agriculture Census 2015-16 (DA&FW)
- PMFBY claim-settlement timelines — official PMFBY portal statistics
- Coimbatore/Pollachi rainfall normals — IMD
- Maize phenology and water requirements — TNAU Agritech Portal / ICAR

Assign this to **Dev D at H24**. A wrong statistic in front of a domain judge undoes an otherwise
strong demo.
