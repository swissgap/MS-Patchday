import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta
import time

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="Microsoft Patchday – FortiProxy Live Monitor",
    page_icon="🧱",
    layout="centered"
)

st.title("🧱 Microsoft Patchday – FortiProxy Live Monitor")
st.caption("Live-Daten von Microsoft Security Update Guide (MSRC)")

# -------------------------------------------------
# Helper: Patchday
# -------------------------------------------------
def second_tuesday(year, month):
    d = date(year, month, 1)
    while d.weekday() != 1:
        d += timedelta(days=1)
    return d + timedelta(days=7)

def next_patchday():
    today = date.today()
    for y in range(today.year, today.year + 2):
        for m in range(1, 13):
            pd_day = second_tuesday(y, m)
            if pd_day >= today:
                return pd_day

# -------------------------------------------------
# MSRC API Fetch
# -------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_msrc_updates():
    """
    Holt echte Microsoft Security Updates (MSRC)
    """
    url = "https://api.msrc.microsoft.com/sug/v2.0/en-US/affectedProduct"
    headers = {
        "Accept": "application/json"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data
    except Exception as e:
        return {"error": str(e)}

def extract_patchday_updates(raw):
    """
    Filtert relevante Patchday-Informationen
    """
    results = []

    if "value" not in raw:
        return results

    for item in raw["value"]:
        results.append({
            "Produkt": item.get("productName"),
            "Produkt Familie": item.get("productFamily"),
            "Release Datum": item.get("releaseDate", "unbekannt"),
            "Impact": "Security Update / Patchday relevant"
        })

    return pd.DataFrame(results)

# -------------------------------------------------
# Patchday Core
# -------------------------------------------------
patchday = next_patchday()
today = date.today()
days_left = (patchday - today).days

# -------------------------------------------------
# Header Info
# -------------------------------------------------
st.subheader("⏰ Patchday Status")

st.metric(
    "Nächster Patchday",
    patchday.strftime("%d.%m.%Y"),
    f"in {days_left} Tagen"
)

# -------------------------------------------------
# Update Button
# -------------------------------------------------
st.subheader("🔄 Microsoft Live-Daten")

if st.button("Jetzt Microsoft-Daten aktualisieren"):
    st.cache_data.clear()
    with st.spinner("Microsoft Security Update Guide wird abgefragt …"):
        time.sleep(1)

raw_data = fetch_msrc_updates()

# -------------------------------------------------
# API Status
# -------------------------------------------------
if "error" in raw_data:
    st.error(f"❌ MSRC API nicht erreichbar: {raw_data['error']}")
    st.info("Patchday-Erinnerung funktioniert weiterhin ohne API.")
else:
    st.success("✅ Echte Microsoft-Daten erfolgreich geladen")

    df = extract_patchday_updates(raw_data)

    st.subheader("📦 Aktuelle Microsoft Security Updates")

    if df.empty:
        st.warning("Noch keine Patchday-Daten veröffentlicht.")
    else:
        st.dataframe(
            df.head(50),
            use_container_width=True,
            hide_index=True
        )

# -------------------------------------------------
# FortiProxy Impact
# -------------------------------------------------
st.error("""
⚠️ **FortiProxy Impact Warning**

Sobald Microsoft Updates veröffentlicht:
- 📈 Massiver Traffic zu Microsoft CDNs
- 🔐 TLS & SSL Inspection Last steigt stark
- 🧱 Proxy Sessions explodieren

➡️ **Empfehlung:** Bypass / Reduced Inspection aktivieren
""")

# -------------------------------------------------
# Recommendations
# -------------------------------------------------
with st.expander("🧱 FortiProxy – Empfohlene Domains (Bypass)"):
    st.markdown("""
