import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta, datetime
import time
import socket

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="FortiProxy Patchday Monitor",
    page_icon="🧱",
    layout="centered"
)

st.title("🧱 Microsoft Patchday – FortiProxy Monitor")
st.caption("High-Impact Updates & Live Network Check")

# -----------------------------
# High-Impact Kategorien
# -----------------------------
HIGH_IMPACT_KEYWORDS = {
    "Windows": ["windows"],
    "Defender": ["defender", "security intelligence"],
    "Office": ["office", "microsoft 365", "m365"]
}

IMPACT_SCORES = {
    "Windows": 5,
    "Defender": 4,
    "Office": 3
}

ALL_CATEGORIES = ["Windows", "Defender", "Office", "Other"]

# -----------------------------
# Helper Functions
# -----------------------------
def second_tuesday(year, month):
    d = date(year, month, 1)
    while d.weekday() != 1:  # Dienstag
        d += timedelta(days=1)
    return d + timedelta(days=7)

def next_patchday():
    today = date.today()
    for y in range(today.year, today.year + 2):
        for m in range(1, 13):
            pd_day = second_tuesday(y, m)
            if pd_day >= today:
                return pd_day

def patchday_window(patchday):
    start = datetime.combine(patchday, datetime.min.time())
    end = start + timedelta(days=1)
    return start, end

@st.cache_data(ttl=3600)
def fetch_msrc_updates():
    """Holt MSRC Security Updates"""
    url = "https://api.msrc.microsoft.com/sug/v2.0/en-US/affectedProduct"
    headers = {"Accept": "application/json"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def classify_high_impact_releases(raw_data, patchday):
    """Filtert MSRC API auf High-Impact Releases"""
    results = []
    columns = ["Kategorie", "Produkt", "Release", "Proxy Impact", "Impact Score"]
    if "value" not in raw_data:
        return pd.DataFrame(results, columns=columns)
    
    window_start, window_end = patchday_window(patchday)
    for item in raw_data["value"]:
        release_str = item.get("releaseDate")
        product_name = item.get("productName") or ""
        product = product_name.lower()
        if not release_str:
            continue
        try:
            release_dt = datetime.fromisoformat(release_str.replace("Z",""))
        except ValueError:
            continue
        if not (window_start <= release_dt < window_end):
            continue
        category_matched = False
        for category, keywords in HIGH_IMPACT_KEYWORDS.items():
            if any(k in product for k in keywords):
                results.append({
                    "Kategorie": category,
                    "Produkt": product_name,
                    "Release": release_dt.strftime("%d.%m.%Y %H:%M"),
                    "Proxy Impact": "HIGH",
                    "Impact Score": IMPACT_SCORES[category]
                })
                category_matched = True
        if not category_matched:
            results.append({
                "Kategorie": "Other",
                "Produkt": product_name,
                "Release": release_dt.strftime("%d.%m.%Y %H:%M"),
                "Proxy Impact": "LOW",
                "Impact Score": 1
            })
    return pd.DataFrame(results, columns=columns)

def patchday_traffic_light(days_to_patchday, high_impact_count, network_warning=False):
    """Ampel Logik + Network Warning berücksichtigt"""
    if network_warning:
        return "🔴 ROT", "WARNUNG: Abweichende Domains/IPs erkannt! Sofortige Anpassung notwendig!"
    if high_impact_count > 0:
        return "🔴 ROT", "Microsoft hat Security Updates veröffentlicht – Proxy Impact AKTIV"
    if days_to_patchday <= 1:
        return "🟠 ORANGE", "Patchday – Releases noch nicht sichtbar, Monitoring aktiv"
    if days_to_patchday <= 3:
        return "🟠 ORANGE", "Patchday steht bevor – Proxy & Capacity vorbereiten"
    return "🟢 GRÜN", "Kein erhöhter Microsoft Update Traffic erwartet"

def patchday_category_preview():
    """Vorschau für nächste Patchday-Kategorien"""
    preview_data = []
    for cat in ALL_CATEGORIES:
        impact = "HIGH" if cat in HIGH_IMPACT_KEYWORDS else "LOW"
        preview_data.append({
            "Kategorie": cat,
            "Erwarteter Impact": impact
        })
    return pd.DataFrame(preview_data)

def patchday_network_preview():
    """Vorschau bekannte Domains für Patchday"""
    preview_data = [
        {"Kategorie": "Windows", "Typ": "CDN / Patchday", "URL/IP": "*.windowsupdate.microsoft.com"},
        {"Kategorie": "Windows", "Typ": "CDN / Patchday", "URL/IP": "*.download.windowsupdate.com"},
        {"Kategorie": "Windows", "Typ": "CDN / Patchday", "URL/IP": "*.delivery.mp.microsoft.com"},
        {"Kategorie": "Office", "Typ": "CDN", "URL/IP": "*.officecdn.microsoft.com"},
        {"Kategorie": "Office", "Typ": "CDN", "URL/IP": "officecdn.microsoft.com.edgesuite.net"},
        {"Kategorie": "Defender", "Typ": "Update / Intelligence", "URL/IP": "*.wdcp.microsoft.com"},
        {"Kategorie": "Defender", "Typ": "Update / Intelligence", "URL/IP": "*.dl.delivery.mp.microsoft.com"},
    ]
    return pd.DataFrame(preview_data)

def resolve_ips(domain_pattern):
    """Wildcard Domain → Basisdomain → IP Lookup"""
    domain = domain_pattern.replace("*.", "")
    try:
        return socket.gethostbyname_ex(domain)[2]
    except Exception:
        return []

# -----------------------------
# Patchday Berechnen
# -----------------------------
patchday = next_patchday()
today = date.today()
days_left = (patchday - today).days

st.subheader("⏰ Patchday Status")
st.metric("Nächster Patchday", patchday.strftime("%d.%m.%Y"), f"in {days_left} Tagen")

# -----------------------------
# Microsoft Updates laden
# -----------------------------
st.subheader("🔄 Microsoft Live-Daten")
if st.button("Jetzt Microsoft-Daten aktualisieren"):
    st.cache_data.clear()
    with st.spinner("Microsoft Security Update Guide wird abgefragt …"):
        time.sleep(1)

raw_data = fetch_msrc_updates()

if "error" in raw_data:
    st.error(f"❌ MSRC API nicht erreichbar: {raw_data['error']}")
    st.info("Patchday-Erinnerung funktioniert weiterhin ohne API.")
    df_high = pd.DataFrame(columns=["Kategorie", "Produkt", "Release", "Proxy Impact", "Impact Score"])
else:
    st.success("✅ Echte Microsoft-Daten erfolgreich geladen")
    df_high = classify_high_impact_releases(raw_data, patchday)

# -----------------------------
# High-Impact Releases
# -----------------------------
if "Kategorie" in df_high.columns:
    high_impact_count = len(df_high[df_high["Kategorie"].isin(HIGH_IMPACT_KEYWORDS)])
else:
    high_impact_count = 0

# -----------------------------
# Netzwerk / Live IP Check
# -----------------------------
st.subheader("🌐 Netzwerk-Vorschau & Live IP Check")
df_network_preview = patchday_network_preview()

network_warning = False
ip_results = []

with st.expander("Domains / Live IPs prüfen"):
    st.info("Wildcard Domains werden auf Basisdomain geprüft")
    for row in df_network_preview.itertuples():
        ips = resolve_ips(row._3)
        if not ips:
            network_warning = True  # Warnung wenn IP nicht auflösbar
        ip_results.append({"Kategorie": row.Kategorie, "Domain": row._3, "Gefundene IPs": ", ".join(ips)})
    df_ip = pd.DataFrame(ip_results)
    st.table(df_ip)

# -----------------------------
# Ampel inklusive Network Warning
# -----------------------------
ampel, ampel_text = patchday_traffic_light(days_left, high_impact_count, network_warning)
st.subheader("🚦 Proxy Traffic Ampel")
if "ROT" in ampel:
    st.error(f"**{ampel}** – {ampel_text}")
elif "ORANGE" in ampel:
    st.warning(f"**{ampel}** – {ampel_text}")
else:
    st.success(f"**{ampel}** – {ampel_text}")

# -----------------------------
# High-Impact Releases Tabelle
# -----------------------------
st.subheader("🔥 High-Impact Patchday Releases")
if df_high.empty:
    st.info("Noch keine Windows / Defender / Office Releases erkannt.")
else:
    st.dataframe(df_high, hide_index=True, use_container_width=True)

# -----------------------------
# Vorschau: Kategorien nächster Patchday
# -----------------------------
st.subheader("🔮 Vorschau – Kategorien nächster Patchday")
df_preview = patchday_category_preview()
st.table(df_preview)

# -----------------------------
# FortiProxy Empfehlungen
# -----------------------------
st.subheader("🧱 FortiProxy – Empfehlung (High-Impact Fokus)")
with st.expander("Domains / Bypass Settings"):
    st.markdown("""
**High-Impact Domains für Bypass / Reduced Inspection:**

- *.windowsupdate.microsoft.com  
- *.update.microsoft.com  
- *.download.windowsupdate.com  
- *.officecdn.microsoft.com  
- *.delivery.mp.microsoft.com  
- *.wdcp.microsoft.com

**FortiProxy Settings:**
- SSL Inspection: ❌ OFF / Bypass  
- AV: ✔ Flow-based  
- Logging: ❌ Minimal  
- Proxy Caching aktivieren (optional)
""")

# -----------------------------
# Footer
# -----------------------------
st.caption(
    "Live MSRC Daten | High-Impact Patchday Monitoring | FortiProxy Ops"
)
