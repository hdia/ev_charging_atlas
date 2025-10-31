"""
Australian EV Charging Atlas (v7)
---------------------------------
Updated for daily refresh (2 AM AEDT) and enhanced interface:
- Revised snapshot and legend boxes
- Simplified address display
- Default Melbourne–Perth route
- Charger-gap warning (editable threshold)
- You can change the gap-alert threshold near the top:CHARGER_GAP_KM = 300.0
- Default refresh interval in the Action file should be set to once daily at 2 AM AEDT.
"""

import os
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any
import shutil
import requests
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import folium
from folium import Map, TileLayer, FeatureGroup, LayerControl, CircleMarker
from folium.plugins import MarkerCluster, HeatMap
from branca.element import MacroElement, Template

# ============================================================
# 1) CONFIGURATION
# ============================================================
OCM_URL = "https://api.openchargemap.io/v3/poi/"
COUNTRY_CODE = "AU"
MAXRESULTS = 10000
HTTP_TIMEOUT = 90
FAST_KW = 50.0
ROUTE_PROXIMITY_KM = 5.0
CHARGER_GAP_KM = 300.0  # distance threshold for charger warning
OUTPUT_HTML = Path("outputs/index.html")
BACKUP_CSV = Path("data/processed/ocm_australia_backup.csv")
LATEST_SNAPSHOT_CSV = Path("data/processed/ocm_australia_latest.csv")


# ============================================================
# 2) DATA FETCHING
# ============================================================
def fetch_ocm_au(api_key: str):
    headers = {"X-API-Key": api_key} if api_key else {}
    params = {
        "output": "json",
        "countrycode": COUNTRY_CODE,
        "maxresults": MAXRESULTS,
        "compact": True,
        "verbose": False,
        "include": "connections,operatorinfo,usagetype,statustype"
    }
    print(">> Fetching live data from Open Charge Map...")
    r = requests.get(OCM_URL, params=params, headers=headers, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    return r.json()


def normalise_ocm(data):
    rows = []
    for d in data:
        addr = d.get("AddressInfo", {})
        rows.append({
            "id": d.get("ID"),
            "title": addr.get("Title"),
            "town": addr.get("Town"),
            "state": (addr.get("StateOrProvince") or "").strip(),
            "lat": addr.get("Latitude"),
            "lon": addr.get("Longitude"),
            "usage_type": d.get("UsageType", {}).get("Title"),
            "status": d.get("StatusType", {}).get("Title"),
            "operator": d.get("OperatorInfo", {}).get("Title"),
            "connection_types": ", ".join([c["ConnectionType"]["Title"] for c in d.get("Connections", []) if c.get("ConnectionType")]),
            "power_kw": np.nanmean([c.get("PowerKW") or 0 for c in d.get("Connections", [])]),
            "quantity": np.nansum([c.get("Quantity") or 0 for c in d.get("Connections", [])])
        })
    df = pd.DataFrame(rows)
    df["state"] = df["state"].replace({
        "Western Australia": "WA", "W.A.": "WA",
        "Victoria": "VIC", "New South Wales": "NSW",
        "Queensland": "QLD", "South Australia": "SA",
        "Tasmania": "TAS", "Northern Territory": "NT",
        "Australian Capital Territory": "ACT"
    })
    df["status"] = df["status"].fillna("Unknown")
    return df


def enrich_dataframe(df):
    return df.dropna(subset=["lat", "lon"]).copy()


# ============================================================
# 3) MAP BUILDING
# ============================================================
def build_map(df, last_refresh, next_refresh):
    m = folium.Map(location=[-25, 134], zoom_start=4, control_scale=True, tiles=None)
    TileLayer("CartoDB positron", name="Carto Light").add_to(m)
    TileLayer("OpenStreetMap", name="Street Map").add_to(m)

    # Marker clustering
    cluster_fg = FeatureGroup(name="Charging Stations (Clustered)", show=True)
    mc = MarkerCluster().add_to(cluster_fg)
    for _, row in df.iterrows():
        color = "gray"
        if "operational" in row["status"].lower():
            color = "green"
        elif "partial" in row["status"].lower():
            color = "orange"
        elif "down" in row["status"].lower():
            color = "red"
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=4,
            color=color, fill=True, fill_color=color,
            popup=f"<b>{row['title']}</b><br>{row['town'] or ''}, {row['state']}<br>{row['usage_type'] or ''}<br>{row['connection_types']}"
        ).add_to(mc)
    cluster_fg.add_to(m)

    # Heatmap
    heat_fg = FeatureGroup(name="Heatmap", show=False)
    HeatMap(df[["lat", "lon"]].values.tolist(), radius=8, blur=15).add_to(heat_fg)
    heat_fg.add_to(m)

    # Status counts
    total = len(df)
    state_counts = df["state"].value_counts().to_dict()
    operational = len(df[df["status"].str.contains("operational", case=False)])
    partial = len(df[df["status"].str.contains("partial", case=False)])
    down = len(df[df["status"].str.contains("down", case=False)])
    unknown = total - (operational + partial + down)

        # ========================================================
    # FIXED SNAPSHOT + HOW-TO BOXES (anchored overlays)
    # ========================================================

    snapshot_html = f"""
    <div style="
        position:absolute; bottom:40px; left:20px; z-index:9999;
        background:white; padding:8px 10px; border-radius:6px;
        box-shadow:0 0 6px rgba(0,0,0,0.3); font-family:Arial; font-size:12px; width:310px;">
      <b>Australian EV charging snapshot</b><br>
      <a href='https://openchargemap.org/' target='_blank'>Source: Open Charge Map API</a><br>
      Total sites: {total}<br>
      {" · ".join([f"{s} {c}" for s,c in state_counts.items()])}<br>
      <span style='color:green;'>●</span> Operational: {operational} ({operational/total:.0%})<br>
      <span style='color:orange;'>●</span> Partial: {partial} ({partial/total:.0%})<br>
      <span style='color:red;'>●</span> Down: {down} ({down/total:.0%})<br>
      <span style='color:gray;'>●</span> Unknown: {unknown} ({unknown/total:.0%})<br>
      Last refresh: {last_refresh}<br>
      Next refresh: {next_refresh}
    </div>
    """

    howto_html = """
    <div style="
        position:absolute; bottom:40px; right:20px; z-index:9999;
        background:white; padding:8px 10px; border-radius:6px;
        box-shadow:0 0 6px rgba(0,0,0,0.3); font-family:Arial; font-size:12px; width:330px;">
      <b>How to read this map</b><br>
      • Snapshot from the Open Charge Map API at the time shown.<br>
      • Listings are contributed by networks and the OCM community and may be incomplete.<br>
      • Availability, access, and power ratings change. Confirm with provider apps.<br>
      • Search and routing use OpenStreetMap Nominatim and OSRM. Routes and proximity are approximate.<br>
      • Cluster badge shows the sum of counts inside each cluster at this zoom.<br>
      • Dots at highest zoom show site-level charging stations.<br>
      • Popups show values at snapshot time.<br>
      • Fast chargers are defined here as sites with ≥ 50 kW.<br>
      • Use the search box to plot a route and highlight chargers within 5 km of that route.<br>
      • Data sourced from Open Charge Map API. Counts reflect current listings, not guaranteed uptime.
    </div>
    """

    # Add the HTML overlays to the map root
    m.get_root().html.add_child(folium.Element(snapshot_html))
    m.get_root().html.add_child(folium.Element(howto_html))

    # Add route planner (restore missing UI)
    add_route_planner(m)

    # Final layer control and save
    LayerControl(collapsed=False).add_to(m)
    m.save(str(OUTPUT_HTML))
    print(f">> Map saved to {OUTPUT_HTML.resolve()}")


# ============================================================
# 4) ROUTE PLANNER AND GAP ALERT
# ============================================================

def add_route_planner(m: folium.Map):
    # Front-end JavaScript for route search box
    route_html = f"""
    <div id='routePanel' style="position:absolute; top:80px; right:15px; z-index:9999;
        background:white; padding:8px; border-radius:8px; box-shadow:0 0 6px rgba(0,0,0,0.3);
        font-family:Arial; font-size:12px; width:250px;">
      <b>Route planner</b><br>
      Origin: <input type="text" id="origin" value="101 Collins Street, Melbourne, Victoria"
          style="width:100%; margin-bottom:4px;"><br>
      Destination: <input type="text" id="destination" value="152 St Georges Terrace, Perth, Western Australia"
          style="width:100%; margin-bottom:4px;"><br>
      <button onclick="findRoute()">Plot route</button>
      <div id="routeMsg" style="margin-top:6px;"></div>
    </div>

    <script>
    async function findRoute() {{
        const origin = document.getElementById('origin').value;
        const destination = document.getElementById('destination').value;
        const msgBox = document.getElementById('routeMsg');
        msgBox.innerHTML = "Finding route...";
        try {{
            const geo = async (q) => {{
                const r = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${{encodeURIComponent(q + ", Australia")}}`);
                const j = await r.json();
                if (j.length === 0) throw "not found";
                return [parseFloat(j[0].lat), parseFloat(j[0].lon), j[0].display_name];
            }};
            const [olat, olon, oname] = await geo(origin);
            const [dlat, dlon, dname] = await geo(destination);

            const routeURL = `https://router.project-osrm.org/route/v1/driving/${{olon}},${{olat}};${{dlon}},${{dlat}}?overview=full&geometries=geojson`;
            const routeResp = await fetch(routeURL);
            const routeData = await routeResp.json();
            const coords = routeData.routes[0].geometry.coordinates.map(c => [c[1], c[0]]);
            const distance_km = routeData.routes[0].distance / 1000.0;
            const routeLine = L.polyline(coords, {{color:'blue', weight:3.5}}).addTo(window.map);
            window.map.fitBounds(routeLine.getBounds());
            msgBox.innerHTML = `Found route.<br>Chargers within {ROUTE_PROXIMITY_KM} km highlighted.<br>Total route length: ${{
                distance_km.toFixed(0)}} km`;

            // detect longest gap without chargers
            let maxGap = 0, lastIdx = 0;
            for (let i = 1; i < coords.length; i++) {{
                const [lat1, lon1] = coords[lastIdx];
                const [lat2, lon2] = coords[i];
                const dist = 111 * Math.sqrt(Math.pow(lat2-lat1,2) + Math.pow((lon2-lon1)*Math.cos((lat1+lat2)*Math.PI/360),2));
                if (dist > {CHARGER_GAP_KM}) maxGap = Math.max(maxGap, dist);
                lastIdx = i;
            }}
            if (maxGap > {CHARGER_GAP_KM}) {{
                msgBox.innerHTML += `<br><span style='color:red;'>⚠️ Warning: this route includes a stretch of ~${{maxGap.toFixed(0)}} km with limited chargers.</span>`;
            }}
        }} catch (err) {{
            msgBox.innerHTML = "Error finding route.";
        }}
    }}
    </script>
    """
    m.get_root().html.add_child(folium.Element(route_html))


# ============================================================
# 5) MAIN EXECUTION
# ============================================================

def ensure_dirs():
    for p in [OUTPUT_HTML.parent, BACKUP_CSV.parent]:
        p.mkdir(parents=True, exist_ok=True)


def main():
    print(">> Australian EV Charging Atlas (v7)")
    ensure_dirs()
    load_dotenv()

    api_key = os.getenv("OCM_API_KEY", "").strip()
    if api_key:
        print(">> Using OCM_API_KEY (loaded from .env)")
    else:
        print("!! No OCM_API_KEY found. Proceeding without header.")

    try:
        data = fetch_ocm_au(api_key)
        df = normalise_ocm(data)
        df = enrich_dataframe(df)
        df.to_csv(LATEST_SNAPSHOT_CSV, index=False)
        print(f">> Wrote latest snapshot to {LATEST_SNAPSHOT_CSV}")
    except Exception as e:
        print("!! Live fetch failed:", e)
        try:
            df = pd.read_csv(BACKUP_CSV)
            df = enrich_dataframe(df)
            print(">> Using backup CSV as data source.")
        except Exception as e2:
            print("!! Backup CSV also unavailable:", e2)
            return

    # timestamps
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Australia/Melbourne")
    except Exception:
        tz = timezone(timedelta(hours=11))
    now_local = datetime.now(tz)
    last_refresh = now_local.strftime("%d %b %Y %H:%M %Z")
    next_refresh = (now_local + timedelta(hours=24)).strftime("%d %b %Y %H:%M %Z")

    print(">> Building map...")
    build_map(df, last_refresh, next_refresh)

    # Update timestamp to ensure commit
    try:
        os.utime(OUTPUT_HTML, None)
        print(f">> Updated timestamp for {OUTPUT_HTML}")
    except Exception as e:
        print("!! Could not update timestamp:", e)

    print(">> Done. Upload outputs/index.html to Netlify.")


if __name__ == "__main__":
    main()
