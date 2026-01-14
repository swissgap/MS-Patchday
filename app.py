import streamlit as st
import pandas as pd
from datetime import date, timedelta

st.set_page_config(
    page_title="Microsoft Patchday Übersicht",
    page_icon="🩹",
    layout="centered"
)

st.title("🩹 Microsoft Patchday Übersicht")
st.caption("Automatische Berechnung der Microsoft Patchdays (2. Dienstag im Monat)")

# -----------------------------
# Hilfsfunktionen
# -----------------------------
def second_tuesday(year, month):
    """Berechnet den zweiten Dienstag eines Monats"""
    d = date(year, month, 1)
    while d.weekday() != 1:  # Dienstag = 1
        d += timedelta(days=1)
    return d + timedelta(days=7)

def generate_patchdays(year):
    data = []
    for month in range(1, 13):
        patchday = second_tuesday(year, month)
        data.append({
            "Jahr": year,
            "Monat": patchday.strftime("%B"),
            "Datum": patchday.strftime("%d.%m.%Y"),
            "Was wird gemacht": (
                "Sicherheitsupdates für Windows, "
                "Office, Exchange, Edge & .NET. "
                "Behebung kritischer und wichtiger CVEs."
            )
        })
    return pd.DataFrame(data)

# -----------------------------
# Auswahl
# -----------------------------
year = st.selectbox(
    "📅 Jahr auswählen",
    options=range(date.today().year - 1, date.today().year + 4),
    index=1
)

df = generate_patchdays(year)

# -----------------------------
# Anzeige nächster Patchday
# -----------------------------
today = date.today()
next_patchday = df.copy()
next_patchday["Datum_obj"] = pd.to_datetime(next_patchday["Datum"], dayfirst=True)
next_patchday = next_patchday[next_patchday["Datum_obj"].dt.date >= today]

if not next_patchday.empty:
    next_row = next_patchday.iloc[0]
    st.success(
        f"🔔 **Nächster Patchday:** {next_row['Datum']} "
        f"({next_row['Monat']} {year})"
    )
else:
    st.info("Für dieses Jahr stehen keine weiteren Patchdays an.")

# -----------------------------
# Tabelle
# -----------------------------
st.subheader("📊 Patchday-Übersicht")
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

# -----------------------------
# Erklärung
# -----------------------------
with st.expander("🛠 Was passiert am Microsoft Patchday?"):
    st.markdown("""
**Am Microsoft Patchday veröffentlicht Microsoft:**

- 🔐 Sicherheitsupdates (kritisch & wichtig)
- 🪟 Windows-Updates (Client & Server)
- 📦 Updates für:
  - Microsoft Office
  - Exchange Server
  - SharePoint
  - .NET Framework
  - Microsoft Edge
- 🧯 Fixes für bekannte Schwachstellen (CVEs)
- 📢 Security Advisories & Release Notes

👉 **Best Practice:**  
Testen → Freigeben → Rollout → Monitoring
""")

st.caption("© IT Operations | Patch & Vulnerability Management")
