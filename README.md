# Australian EV Charging Monitor

A live map of electric vehicle chargers across Australia, updated automatically every 24 hours.  
Built from open data using the **[Open Charge Map API](https://openchargemap.org/)** and **[OpenStreetMap OSRM](https://project-osrm.org/)**.

---

## ⚙️ Setup & Hosting

### 1. Repository setup
Clone or fork this repository, ensuring it contains:
- `build_ev_monitor.py` (or the current Python build script)
- `requirements.txt`
- `.github/workflows/rebuild.yml`
- `data/` and `outputs/` folders

### 2. Automatic rebuild
GitHub Actions (see `.github/workflows/rebuild.yml`) runs the Python script every 24 hours, regenerates the map, and commits `outputs/index.html`.

You can also trigger it manually via:
```
Actions → Rebuild and Deploy EV Charging Monitor → Run workflow
```

### 3. Hosting on GitHub Pages
The site is hosted directly via **GitHub Pages** using the Actions deploy pipeline.  
Once the workflow runs successfully, your live site will be available at:

> https://hdia.github.io/ev_charging_monitor/

---

## 🗺️ Data Notes

- Data source: [Open Charge Map API](https://openchargemap.org/)
- Routing: [OSRM](https://project-osrm.org/)
- Geocoding: [OpenStreetMap Nominatim](https://nominatim.org/)
- These are open-data services with voluntary reporting. Some operators may not list all of their charging sites or update them regularly, so counts and locations may differ from proprietary maps.

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
