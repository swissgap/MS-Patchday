import streamlit as st
import pandas as pd
from datetime import date, timedelta

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="Microsoft Patchday Reminder & Proxy Impact",
    page_icon="🚦",
    layout="centered"
)

st.title("🚦 Microsoft Patchday – Reminder & Proxy Impact")
st.caption("Frühwarnsystem für IT-Betrieb, Proxy & Netzwerk")

# -------------------------------------------------
# Helper Functions
# -------------------------------------------------
def second_tuesday(year, month):
    d = date(year, month, 1)
    while d.weekday() != 1:  # Tuesday
        d += timedelta(days=1)
    return d + timedelta(days=7)

def next_patchday(today):
    year = today.year
    for _ in range(24):
        for month in range(1, 13):
            pd_day = second_tuesday(year, month)
            if pd_day >= today:
                return pd_day
        year += 1

def impact_level(days_left):
    if days_left <= 1:
        return "🔴 HIGH", "Sehr hoher Microsoft-Traffic zu erwarten"
    elif days_left <= 3:
        return "🟠 MEDIUM", "Deutlich erhöhter Proxy- & CDN-Traffic"
    else:
        return "🟢 LOW", "Normalbetrieb – Vorbereitung empfohlen"

# -------------------------------------------------
# Calculate Patchday
# -------------------------------------------------
today = date.today()
patchday = next_patchday(today)
days_left = (patchday - today).days
level, impact_text = impact_level(days_left)

# -------------------------------------------------
# Reminder Section
# -------------------------------------------------
st.subheader("⏰ Nächster Microsoft Patchday")

st.metric(
    label="Patchday Datum",
    value=patchday.strftime("%d.%m.%Y"),
    delta=f"in {days_left} Tagen"
)

st.markdown(f"""
### 🚦 Impact-Einschätzung
**Stufe:** {level}  
**Erwartung:** {impact_text}
""")

# -------------------------------------------------
# Proxy Impact Warning
# -------------------------------------------------
st.error("""
⚠️ **ACHTUNG: Proxy- & Netzwerk-Impact**

Am Microsoft Patchday ist mit **massiv erhöhtem ausgehendem Traffic**
in Richtung Microsoft-Cloud & CDN zu rechnen.

**Typische Auswirkungen:**
- Erhöhte Proxy-CPU & Session-Zahlen
- Bandbreiten-Sättigung
- Verzögerte Updates / Client-Timeouts
- Beeinträchtigung anderer Cloud-Dienste
""")

# -------------------------------------------------
# Preparation Checklist
# -------------------------------------------------
with st.expander("🛠 Operative Vorbereitung (empfohlen)"):
    st.markdown("""
**Vor Patchday (T-3 bis T-1):**
- ✅ Proxy- & Firewall-Health prüfen
- ✅ Bandbreiten- & QoS-Regeln kontrollieren
- ✅ SSL Inspection Ausnahmen prüfen
- ✅ Windows Update Caching (WSUS / Delivery Optimization)

**Am Patchday:**
- 👀 Live-Monitoring (Sessions, Throughput, Errors)
- 📊 Proxy-Dashboards offen halten
- 🧯 Incident-Bereitschaft sicherstellen

**Nach Patchday:**
- 📉 Traffic normalisiert sich i.d.R. nach 24–72h
- 📝 Lessons Learned dokumentieren
""")

# -------------------------------------------------
# Patchday Preview
# -------------------------------------------------
st.subheader("📅 Patchday Vorschau")

preview = []
for i in range(6):
    future = patchday + timedelta(days=30 * i)
    pd_day = second_tuesday(future.year, future.month)
    preview.append({
        "Monat": pd_day.strftime("%B %Y"),
        "Datum": pd_day.strftime("%d.%m.%Y"),
        "Typischer Impact": "Erhöhter Microsoft Update & CDN Traffic"
    })

df = pd.DataFrame(preview)
st.dataframe(df, hide_index=True, use_container_width=True)

# -------------------------------------------------
# Footer
# -------------------------------------------------
st.caption(
    "🚨 Reminder-App für IT Operations | Fokus: Proxy, Firewall, Netzwerk, Cloud Access"
)

