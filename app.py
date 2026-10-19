"""
AquaSky — Cloud-Seeding Decision Dashboard (prototype)
=======================================================
STEN 1000 Stage 2 — functional prototype demonstration.

What this does:
    Reads sample environmental data for 5 candidate zones, runs each
    zone through a transparent rules engine, and outputs a seeding
    recommendation: GO / MARGINAL / NO-GO, plus where and when to seed.

IMPORTANT: every number in this demo is SAMPLE / SYNTHETIC data made up
for the demonstration. Nothing here is real sensor data.

Run it:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd

# ---------------------------------------------------------------------------
# Rules engine
# ---------------------------------------------------------------------------
# The engine is deliberately simple on purpose: six rules, each worth
# points. Add up the points -> suitability score out of 95 -> verdict.
# Two "veto" conditions force an automatic NO-GO no matter the score:
#   - almost no cloud cover (nothing to seed)
#   - dangerous wind (seeding material would drift off target)
#
# To tweak the demo, just change the numbers below — everything in the
# dashboard updates automatically.

MAX_SCORE = 95


def evaluate_zone(readings: dict) -> dict:
    """Score one zone and return the full recommendation.

    readings: dict with keys temperature_c, humidity_pct, cloud_cover_pct,
              wind_kmh, soil_moisture_pct, snowpack_cm
    returns: dict with verdict, score, confidence_pct, reasons (list of
             (passed, text) tuples), location, and timing.
    """
    reasons = []          # (passed: bool, explanation: str)
    contributions = {}    # rule name -> points earned (for the bar chart)
    score = 0
    veto = None           # if set, verdict is NO-GO no matter the score

    # --- Rule 1: Cloud cover (need clouds to seed!) ---
    cloud = readings["cloud_cover_pct"]
    if cloud >= 60:
        pts = 25
        reasons.append((True, f"Cloud cover {cloud}% ≥ 60% — thick clouds, ideal seeding target ✓"))
    elif cloud >= 40:
        pts = 15
        reasons.append((True, f"Cloud cover {cloud}% ≥ 40% — enough cloud to work with ✓"))
    elif cloud >= 20:
        pts = 5
        reasons.append((False, f"Cloud cover {cloud}% below 40% — thin clouds, weak target ✗"))
    else:
        pts = 0
        veto = f"Cloud cover only {cloud}% — there is nothing to seed"
        reasons.append((False, f"Cloud cover {cloud}% < 20% minimum — VETO ✗"))
    contributions["Cloud cover"] = pts
    score += pts

    # --- Rule 2: Relative humidity (moist air = clouds can grow) ---
    hum = readings["humidity_pct"]
    if hum >= 75:
        pts = 20
        reasons.append((True, f"Humidity {hum}% ≥ 75% — moist air, clouds likely to grow ✓"))
    elif hum >= 60:
        pts = 12
        reasons.append((True, f"Humidity {hum}% ≥ 60% — decent moisture ✓"))
    elif hum >= 45:
        pts = 5
        reasons.append((False, f"Humidity {hum}% below 60% — air is fairly dry ✗"))
    else:
        pts = 0
        reasons.append((False, f"Humidity {hum}% < 45% — too dry for seeding ✗"))
    contributions["Humidity"] = pts
    score += pts

    # --- Rule 3: Temperature (seeding works best near freezing) ---
    temp = readings["temperature_c"]
    if -5 <= temp <= 2:
        pts = 20
        reasons.append((True, f"Temperature {temp}°C in the −5 to 2°C sweet spot — supercooled clouds ✓"))
    elif -10 <= temp <= 6:
        pts = 10
        reasons.append((True, f"Temperature {temp}°C workable, but outside the ideal band ✓"))
    else:
        pts = 0
        reasons.append((False, f"Temperature {temp}°C outside the seedable range ✗"))
    contributions["Temperature"] = pts
    score += pts

    # --- Rule 4: Wind speed (too windy = material drifts off target) ---
    wind = readings["wind_kmh"]
    if wind <= 15:
        pts = 15
        reasons.append((True, f"Wind {wind} km/h ≤ 15 — calm, material stays on target ✓"))
    elif wind <= 30:
        pts = 8
        reasons.append((True, f"Wind {wind} km/h ≤ 30 — acceptable, some drift ✓"))
    elif wind <= 45:
        pts = 0
        reasons.append((False, f"Wind {wind} km/h over the 30 km/h limit — too much drift ✗"))
    else:
        pts = 0
        veto = f"Wind {wind} km/h — unsafe, seeding material would drift off target"
        reasons.append((False, f"Wind {wind} km/h > 45 km/h — VETO ✗"))
    contributions["Wind"] = pts
    score += pts

    # --- Rule 5: Soil moisture (dry soil = the land actually needs water) ---
    soil = readings["soil_moisture_pct"]
    if soil < 30:
        pts = 10
        reasons.append((True, f"Soil moisture {soil}% < 30% — dry soil, this zone needs the water ✓"))
    elif soil <= 45:
        pts = 5
        reasons.append((True, f"Soil moisture {soil}% — moderately dry ✓"))
    else:
        pts = 0
        reasons.append((False, f"Soil moisture {soil}% — soil is already wet, low need ✗"))
    contributions["Soil moisture"] = pts
    score += pts

    # --- Rule 6: Snowpack (existing snow = winter water storage, small bonus) ---
    snow = readings["snowpack_cm"]
    if snow >= 10:
        pts = 5
        reasons.append((True, f"Snowpack {snow} cm — good winter water storage bonus ✓"))
    elif snow >= 3:
        pts = 2
        reasons.append((True, f"Snowpack {snow} cm — small bonus ✓"))
    else:
        pts = 0
        reasons.append((False, f"Snowpack {snow} cm — no winter storage bonus ✗"))
    contributions["Snowpack"] = pts
    score += pts

    # --- Verdict from the score ---
    if veto is not None:
        verdict = "NO-GO"
        confidence = 95
    elif score >= 65:
        verdict = "GO"
        confidence = min(98, score)
    elif score >= 40:
        verdict = "MARGINAL"
        confidence = score
    else:
        verdict = "NO-GO"
        confidence = max(60, 100 - score)  # very low score = very sure it's a no

    # --- Where and when ---
    zone_name = readings["zone"]
    location = f"Central {zone_name} — release at cloud-base altitude (~1,500 m)"
    if veto and "Wind" in veto:
        timing = "HOLD — wait until wind drops below 30 km/h, then re-check in 2 hours."
    elif verdict == "GO":
        timing = "Optimal window: the next 3 hours — conditions are stable."
    elif verdict == "MARGINAL":
        timing = "Conditional — re-check in 2 hours; seed only if cloud cover climbs above 60%."
    else:
        timing = "No window today — conditions are unsuitable for seeding."

    return {
        "verdict": verdict,
        "score": score,
        "max_score": MAX_SCORE,
        "confidence_pct": confidence,
        "reasons": reasons,
        "contributions": contributions,
        "location": location,
        "timing": timing,
        "veto": veto,
    }


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

st.set_page_config(page_title="AquaSky — Seeding Decision Dashboard", layout="wide")

st.title("🌧️ AquaSky — Cloud-Seeding Decision Dashboard")
st.caption("Prototype demonstration — every number shown is **sample / synthetic data**, not real sensor data.")

# Load the sample data (one row per candidate zone)
data = pd.read_csv("sample_data.csv")

# Score every zone once so the ranking table is ready
results = {}
for _, row in data.iterrows():
    results[row["zone"]] = evaluate_zone(row.to_dict())

# --- Sidebar: zone picker + how-it-works ---
zone = st.sidebar.selectbox("Select candidate zone", data["zone"].tolist())

with st.sidebar.expander("⚙️ How the engine decides"):
    st.write("""
    Six rules, each worth points (max 95). **Veto** = automatic NO-GO.

    | Rule | Full pts | Veto |
    |---|---|---|
    | Cloud cover ≥ 60% | 25 | < 20% |
    | Humidity ≥ 75% | 20 | — |
    | Temp −5 to 2 °C | 20 | — |
    | Wind ≤ 15 km/h | 15 | > 45 km/h |
    | Soil moisture < 30% | 10 | — |
    | Snowpack ≥ 10 cm | 5 | — |

    **GO** ≥ 65 · **MARGINAL** 40–64 · **NO-GO** < 40 or veto.
    """)

# --- Big verdict banner (demo-visible) ---
res = results[zone]
banner_colors = {
    "GO": ("#1a7f37", "#d8f3dc"),
    "MARGINAL": ("#9a6700", "#fff3cd"),
    "NO-GO": ("#b42318", "#fde8e8"),
}
fg, bg = banner_colors[res["verdict"]]
st.markdown(
    f"""
    <div style="background-color:{bg}; border:3px solid {fg}; border-radius:12px;
                padding:18px; text-align:center; margin-bottom:16px;">
        <div style="font-size:20px; color:{fg}; font-weight:600;">{zone}</div>
        <div style="font-size:56px; color:{fg}; font-weight:800; line-height:1.1;">
            {res["verdict"]}
        </div>
        <div style="font-size:18px; color:{fg};">
            Suitability {res["score"]}/{res["max_score"]} · Confidence {res["confidence_pct"]}%
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Where + when ---
col1, col2 = st.columns(2)
with col1:
    st.info(f"📍 **Recommended location:** {res['location']}")
with col2:
    st.warning(f"⏰ **Timing window:** {res['timing']}")

# --- Live readings (sample data) ---
st.subheader("📡 Sensor readings (sample data)")
row = data[data["zone"] == zone].iloc[0]
m1, m2, m3 = st.columns(3)
m1.metric("Temperature", f"{row['temperature_c']} °C")
m2.metric("Relative humidity", f"{row['humidity_pct']} %")
m3.metric("Cloud cover", f"{row['cloud_cover_pct']} %")
m4, m5, m6 = st.columns(3)
m4.metric("Wind speed", f"{row['wind_kmh']} km/h")
m5.metric("Soil moisture", f"{row['soil_moisture_pct']} %")
m6.metric("Snowpack depth", f"{row['snowpack_cm']} cm")

# --- Plain-language reasoning: which rules fired ---
st.subheader("🧠 Why this verdict — rules fired")
for passed, text in res["reasons"]:
    icon = "✅" if passed else "❌"
    st.write(f"{icon} {text}")

# --- Score breakdown chart ---
st.subheader("📊 Score breakdown by rule")
chart_df = pd.DataFrame(
    {"Points earned": res["contributions"]},
)
st.bar_chart(chart_df)

# --- All zones ranked ---
st.subheader("🏁 All zones ranked by suitability")
table_rows = []
for z in data["zone"]:
    r = results[z]
    d = data[data["zone"] == z].iloc[0]
    table_rows.append({
        "Zone": z,
        "Temp (°C)": d["temperature_c"],
        "Humidity (%)": d["humidity_pct"],
        "Cloud (%)": d["cloud_cover_pct"],
        "Wind (km/h)": d["wind_kmh"],
        "Soil (%)": d["soil_moisture_pct"],
        "Snow (cm)": d["snowpack_cm"],
        "Score": f"{r['score']}/{r['max_score']}",
        "_sort": r["score"],
        "Verdict": r["verdict"],
    })
table = pd.DataFrame(table_rows).sort_values("_sort", ascending=False).drop(columns="_sort")
st.dataframe(table, use_container_width=True, hide_index=True)

st.caption("AquaSky prototype · STEN 1000 Stage 2 · All data shown is sample/synthetic.")
