# Australian EV Charging Monitor

A live map of electric vehicle chargers across Australia, updated automatically every 24 hours.  
Built from open data using the **[Open Charge Map API](https://openchargemap.org/)** and **[OpenStreetMap OSRM](https://project-osrm.org/)**.

---

## ⚙️ Setup & Hosting

### 1. Repository setup
Clone or fork this repository, ensuring it contains:
- `build_ev_atlas.py`
- `requirements.txt`
- `.github/workflows/rebuild.yml`
- `data/` and `outputs/` folders

### 2. Automatic rebuild
GitHub Actions (see `.github/workflows/rebuild.yml`) runs the Python script every 24 hours, regenerates the map, and commits `outputs/index.html`.

You can trigger it manually via:
```
Actions → Rebuild → Run workflow
```

### 3. Hosting on GitHub Pages
In your repository:
1. Go to **Settings → Pages**
2. Under “Build and deployment”, choose:
   - **Source:** Deploy from branch  
   - **Branch:** `main` → `/outputs`
3. Save — your site will be available at  
   `https://<your-username>.github.io/ev_charging_monitor/`

---

## 🗺️ Data Notes

- Data source: [Open Charge Map API](https://openchargemap.org/)
- Routing: [OSRM](https://project-osrm.org/)
- Geocoding: [OpenStreetMap Nominatim](https://nominatim.org/)
- These are open-data services with voluntary reporting; some chargers may not be listed or fully up to date.

---

## 🧩 Requirements

```
folium
branca
python-dotenv
pandas
numpy
requests
```

---

## 📝 Credits
Developed at Swinburne University of Technology  
Data © contributors to OpenStreetMap and Open Charge Map
