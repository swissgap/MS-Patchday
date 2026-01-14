import streamlit as st
import pandas as pd
from datetime import date, timedelta
import base64

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="Patchday FortiProxy Impact Monitor",
    page_icon="🧱",
    layout="centered"
)

st.title("🧱 Microsoft Patchday – FortiProxy Impact Monitor")
st.caption("Early Warning & Operations Dashboard für Proxy & Netzwerk")

# -------------------------------------------------
# Helper Functions
# -------------------------------------------------
def second_tuesday(year, month):
    d = date(year, month, 1)
    while d.weekday() != 1:
        d += timedelta(days=1)
    return d + timedelta(days=7)

def get_next_patchday():
    today = date.today()
    for y in range(today.year, today.year + 2):
        for m in range(1, 13):
            pd_day = second_tuesday(y, m)
            if pd_day >= today:
                return pd_day

def impact(days):
    if days <= 0:
        return "🔴 HIGH", "Patchday – Peak Traffic aktiv"
    if days <= 1:
        return "🔴 HIGH", "Extrem hoher Update-Traffic"
    if days <= 3:
        return "🟠 MEDIUM", "Deutlich erhöhter Microsoft-Traffic"
    return "🟢 LOW", "Vorbereitungsphase"

def create_ics(patchday):
    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART;VALUE=DATE:{patchday.strftime('%Y%m%d')}
DTEND;VALUE=DATE:{(patchday + timedelta(days=1)).strftime('%Y%m%d')}
SUMMARY:Microsoft Patchday (FortiProxy Impact)
DESCRIPTION:Erhöhter Microsoft Update Traffic über Proxy
END:VEVENT
END:VCALENDAR
"""
    return base64.b64encode(ics.encode()).decode()

# -------------------------------------------------
# Patchday Calculation
# -------------------------------------------------
today = date.today()
patchday = get_next_patchday()
days_left = (patchday - today).days
level, impact_text = impact(days_left)

# -------------------------------------------------
# Reminder
# -------------------------------------------------
st.subheader("⏰ Patchday Reminder")

st.metric(
    "Nächster Microsoft Patchday",
    patchday.strftime("%d.%m.%Y"),
    f"in {days_left} Tagen"
)

st.markdown(f"""
### 🚦 Impact Level
**Status:** {level}  
**Erwartung:** {impact_text}
""")

# -------------------------------------------------
# Reminder Timeline
# -------------------------------------------------
st.info("""
📢 **Automatische Reminder-Logik**
- **T-3:** Vorbereitung Proxy / Capacity
- **T-1:** Monitoring & Ops-Bereitschaft
- **T-0:** Live-Traffic & Incident-Fokus
""")

# -------------------------------------------------
# Traffic Forecast
# -------------------------------------------------
st.subheader("📊 Erwarteter Proxy-Traffic")

forecast = pd.DataFrame([
    {"Phase": "Normalbetrieb", "Sessions": "1x", "Bandbreite": "1x"},
    {"Phase": "T-3 bis T-1", "Sessions": "1.5–2x", "Bandbreite": "1.3–1.6x"},
    {"Phase": "Patchday", "Sessions": "3–6x", "Bandbreite": "2–4x"},
    {"Phase": "Post Patchday", "Sessions": "1.5–2x", "Bandbreite": "1.2–1.5x"},
])

st.dataframe(forecast, hide_index=True, use_container_width=True)

# -------------------------------------------------
# FortiProxy Recommendations
# -------------------------------------------------
st.subheader("🧱 FortiProxy – Empfohlene Massnahmen")

with st.expander("🔓 Microsoft Update Whitelist / Bypass"):
    st.markdown("""
**Empfohlene Ziele (Domain-based):**
- `*.windowsupdate.microsoft.com`
- `*.update.microsoft.com`
- `*.download.windowsupdate.com`
- `*.officecdn.microsoft.com`
- `*.delivery.mp.microsoft.com`

**Empfehlung:**
- SSL Inspection **bypassen**
- Antivirus **flow-based**
- Logging reduzieren (Performance!)
""")

with st.expander("⚙️ FortiProxy Tuning (Best Practice)"):
    st.markdown("""
- ✔ Proxy Worker & CPU Load prüfen
- ✔ Max Sessions & TCP Timeouts kontrollieren
- ✔ Explicit Proxy bevorzugen
- ✔ Caching aktivieren (falls genutzt)
- ✔ QoS für Business Apps absichern
""")

# -------------------------------------------------
# Calendar Export
# -------------------------------------------------
st.subheader("📅 Patchday in Kalender übernehmen")

ics = create_ics(patchday)
st.markdown(
    f"[📥 ICS-Datei herunterladen](data:text/calendar;base64,{ics})",
    unsafe_allow_html=True
)

# -------------------------------------------------
# Footer
# -------------------------------------------------
st.caption(
    "Designed für FortiProxy | Netzwerk-, Security- & IT-Operations-Teams"
)
