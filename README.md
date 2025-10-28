# Australian EV Charging Atlas

A live, auto-updating map of electric vehicle chargers across Australia, built using data from the **Open Charge Map API**.

---

## 🧭 Overview
This repository rebuilds and redeploys the map every hour using GitHub Actions and Netlify.  
No local setup required once connected — GitHub handles rebuilds, and Netlify hosts the static HTML.

---

## ⚙️ Setup Instructions

### 1. Create GitHub repository
Create a new repo named `ev_charging_atlas` (public or private).

### 2. Add the files
Include:
- `build_ev_atlas.py`
- `requirements.txt`
- `netlify.toml`
- `.github/workflows/rebuild.yml`
- `.env.example` (for local testing)

### 3. Push to GitHub
From your local terminal:
```bash
git init
git remote add origin https://github.com/<your-username>/ev_charging_atlas.git
git add .
git commit -m "Initial upload"
git branch -M main
git push -u origin main
```

### 4. Add your OCM API key
In GitHub → **Settings → Secrets and variables → Actions**,  
create a new secret:
```
Name: OCM_API_KEY
Value: your_actual_key
```

### 5. Deploy on Netlify
- Go to [Netlify](https://www.netlify.com/)
- Create a new site from Git, link this repository
- Set **Publish directory** to `outputs`
- Save and deploy

### 6. Automatic hourly updates
The GitHub Action runs every hour (UTC), regenerates the map, and commits the new HTML.  
Netlify detects the change and auto-deploys.

---

## 📝 Credits
- Data: [Open Charge Map API](https://openchargemap.org/)
- Routing: [OSRM](https://project-osrm.org/)
- Geocoding: [OpenStreetMap Nominatim](https://nominatim.org/)
