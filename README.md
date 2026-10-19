# AquaSky — Cloud-Seeding Decision Dashboard (Prototype)

STEN 1000 Stage 2 functional prototype: sample environmental data goes in,
a seeding recommendation (GO / MARGINAL / NO-GO) comes out.

> **All data in this demo is sample / synthetic** — made up for the
> demonstration. Nothing here is real sensor data.

## How to run

```bash
pip install streamlit pandas
streamlit run app.py
```

Then open the URL it prints (usually http://localhost:8501).

## Files

| File | What it is |
|---|---|
| `app.py` | The Streamlit dashboard + the rules engine (`evaluate_zone`) |
| `sample_data.csv` | The 5 candidate zones and their sample readings |
| `requirements.txt` | Python dependencies for Streamlit Cloud |

## The demo data (designed to show range)

| Zone | Designed outcome |
|---|---|
| Zone A – North Ridge Farmland | **GO** — thick clouds, moist air, calm, dry soil |
| Zone B – Cedar Hollow Forest | **NO-GO** — almost no clouds (veto), too warm, windy |
| Zone C – Lakeshore Flats | **MARGINAL** — decent but not great across the board |
| Zone D – Pinewood Uplands | **GO** — strong winter conditions |
| Zone E – South Valley Orchards | **NO-GO** — thin clouds, warm, windy, wet soil |

## 3-minute demo script (Nov 2 lecture)

**0:00–0:30 — The pitch in one line.**
"AquaSky answers one question: *where and when should we seed clouds today?*
Sample sensor data goes in, the engine gives a GO / MARGINAL / NO-GO, a
location, a timing window, and the reasoning. Everything you see is
sample data — this is the decision logic we're demonstrating."

**0:30–1:00 — The happy path (Zone A → GO).**
Select **Zone A – North Ridge Farmland** in the sidebar. Point at the big
green banner: GO, 95/95, high confidence. Scroll to the reasoning bullets —
read two aloud. Say: "The engine shows its work — every rule that fired, in
plain language."

**1:00–1:45 — The veto (Zone B → NO-GO).**
Switch to **Zone B – Cedar Hollow Forest**. Red banner: "Cloud cover 15% <
20% minimum — VETO." Say: "Even if everything else were perfect, the engine
refuses — there's nothing to seed. That's the safety logic, and it's
automatic."

**1:45–2:15 — The interesting middle (Zone C → MARGINAL).**
Switch to **Zone C – Lakeshore Flats**. Amber banner. Point at the timing
box: *"Conditional — re-check in 2 hours."* Say: "Not every day is a clear
yes or no — the engine tells you exactly what would change the answer."

**2:15–2:45 — The full picture (ranking table).**
Scroll to **"All zones ranked."** Say: "One glance ranks all five candidate
zones — that's the morning briefing a water manager would actually use."

**2:45–3:00 — Close.**
Open the sidebar **"How the engine decides"** expander. "Six rules, 95
points, two vetoes — the whole thing is one readable Python function,
`evaluate_zone`."
