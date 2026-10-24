# Real-World EV Charging Station Placement & Route Planning
### Graded B.Tech CSE "Design and Analysis of Algorithms" (DAA) Semester Project

---

## 1. Project Overview

This project is a **production-grade, real-world Geographic Information System (GIS) application** for Electric Vehicle (EV) Charging Station Placement and Route Planning.

### Core Philosophy:
$$\text{REAL EARTH MAP} + \text{REAL ROADS} + \text{REAL EV STATIONS} + \text{OUR HAND-WRITTEN DAA ALGORITHMS} = \text{ACTUAL WORKING APPLICATION}$$

- **Zero Fake Data:** No hardcoded locations, no synthetic coordinates, no fake charging stations, no fake road distances, and no fabricated statistics.
- **External Real Data Sources:**
  - **OpenStreetMap & Nominatim:** Real-world geocoding and live interactive map tiling (CartoDB Dark Matter / OSM).
  - **Open Charge Map API & OpenStreetMap Infrastructure:** Real physical EV charging stations with operator details, connector specifications, and port quantities.
  - **HeiGIT / OpenRouteService & OSRM:** Actual road-network distance matrices and turn-by-turn driving route geometries.
- **Academic DAA Algorithms (Hand-written in Python, Zero Library Shortcuts):**
  1. **Minimum Spanning Tree (MST):** Hand-written **Kruskal's Algorithm** with Disjoint Set Union (union by rank, two-pass path compression) operating on real road-distance graph edges.
  2. **Shortest Path Routing:** Hand-written **Dijkstra's Algorithm** using a binary min-heap with lazy deletion and edge relaxation.
  3. **0/1 Knapsack Dynamic Programming:** Hand-written **2D Bottom-Up DP** table with backtracking reconstruction and strict inequality tie-breaking to optimize station deployment under a municipal budget.

---

## 2. Architecture & Data Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Leaflet + Dark GIS UI)                │
│  - Real Earth interactive map (pan, zoom, tile attribution)            │
│  - Real search box (Bhubaneswar, Delhi, London, New York, etc.)        │
│  - Stations drawer & editable planning costs/values                    │
│  - Algorithm execution deck & real vector map layers                   │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ HTTP (REST JSON)
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND (backend/main.py)                 │
│  /api/geocode          /api/charging-stations    /api/distance-matrix  │
│  /api/route            /api/mst                  /api/dijkstra         │
│  /api/knapsack         /api/health                                     │
└────────────┬───────────────────────────────────────────────┬───────────┘
             │ Queries Real APIs                             │ Passes Graph
             ▼                                               ▼
┌────────────────────────────────────────┐      ┌────────────────────────┐
│         EXTERNAL REAL DATA APIS        │      │   OUR DAA ALGORITHMS   │
│ - Nominatim (OSM Geocoding)            │      │ 1. Kruskal's MST       │
│ - Open Charge Map API (Real EV POIs)   │      │ 2. Dijkstra Algorithm  │
│ - OpenRouteService / OSRM (Road dist)  │      │ 3. 0/1 Knapsack DP     │
└────────────────────────────────────────┘      └────────────────────────┘
```

---

## 3. Clear Academic Separation: External Data vs Our Algorithms

| Component | Nature / Provider | Responsibility |
|---|---|---|
| **World Map Tiling** | OpenStreetMap / CartoDB Dark Matter | Renders real Earth roads, terrain, and city features with attribution. |
| **Location Geocoding** | Nominatim / OpenRouteService API | Translates user text queries into real latitude & longitude coordinates. |
| **EV Station Metadata** | Open Charge Map / OpenStreetMap | Supplies real station names, addresses, operators, and connector specs. |
| **Driving Distances** | OpenStreetMap OSRM / OpenRouteService | Computes actual driving road distances (meters) and travel durations. |
| **Power Backbone (MST)** | **Our Python Code (`algorithms/mst.py`)** | Computes minimal acyclic high-voltage feeder line backbone. |
| **Access Routing** | **Our Python Code (`algorithms/dijkstra.py`)** | Computes graph shortest path using binary min-heap relaxation. |
| **Budget Optimization** | **Our Python Code (`algorithms/knapsack.py`)** | Solves 0/1 Knapsack DP recurrence $dp[i][w]$ and reconstructs optimal subset. |

---

## 4. How Real Data Flows Through the Algorithms

1. **Step 1 — Search:** The user searches for a city (e.g. `Bhubaneswar` or `Delhi`). Nominatim returns real coordinates: $(20.2603^\circ\text{ N}, 85.8395^\circ\text{ E})$.
2. **Step 2 — Fetch Real Stations:** Backend calls Open Charge Map API for charging stations within the chosen radius. If Open Charge Map key is omitted or zero are found, OpenStreetMap Overpass API is queried. Real markers appear on the map.
3. **Step 3 — User Inputs Costs & Benefits:** The user selects candidate stations and enters their installation costs (₹) and expected public benefit score.
4. **Step 4 — Real Road Graph Construction:** Backend requests the distance matrix from the OSM road routing engine. Edges represent real driving road distances in kilometers.
5. **Step 5 — Kruskal's MST:**
   - Input: $G=(V, E)$ where $w(u, v) = \text{road\_distance\_km}$.
   - Hand-written DSU detects cycles and constructs the minimal power feeder network.
   - Drawn on real map as solid green lines with total backbone km and electrical budget.
6. **Step 6 — Dijkstra's Shortest Path:**
   - User picks Origin and Destination from candidate stations.
   - Our Dijkstra algorithm relaxes graph edges to find the shortest graph path.
   - Turn-by-turn road geometry from the routing engine is rendered on the map.
7. **Step 7 — 0/1 Knapsack DP:**
   - Each candidate's weight $w_i = \text{installation\_cost}_i + \text{feeder\_connection\_cost}_i$ (derived from the shortest incident MST edge).
   - Recurrence: $dp[i][w] = \max(dp[i-1][w], dp[i-1][w-w'_i] + v_i)$.
   - Backtracking identifies the optimal subset. Selected stations pulse on the real map.

---

## 5. Honest Asymptotic Complexity Specifications

| Algorithm | Category | Time Complexity | Space Complexity | Real Invariant / Data Structures |
|---|---|---|---|---|
| **Kruskal's MST** | Greedy / Disjoint Set | $\mathcal{O}(E \log V)$ | $\mathcal{O}(V + E)$ | Sorts real road edges with deterministic tie-breaking. DSU uses rank and two-pass path compression ($\mathcal{O}(\alpha(V))$ amortized). |
| **Dijkstra's Search** | Greedy / Priority Queue | $\mathcal{O}((V + E) \log V)$ | $\mathcal{O}(V + E)$ | Binary min-heap storing `(dist, node_id)`. Lazy deletion of stale entries; $\epsilon$-tolerant relaxation ($10^{-7}$). |
| **0/1 Knapsack** | Dynamic Programming | $\mathcal{O}(n \cdot B')$ *(Pseudo-Polynomial)* | $\mathcal{O}(n \cdot B')$ | Bottom-up 2D matrix ($N \times \text{Scaled Budget}$) enabling backtracking. Scaled capacity $B' = \min(B/g, 200000)$ with provable budget safety. |

---

## 6. Setup & Running Instructions

### Prerequisites
- Python 3.10+
- Dependencies: `fastapi`, `uvicorn`, `requests`, `pydantic`, `python-dotenv`, `pytest`

### Step 1: Install Requirements
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to configure your API keys (the app functions with live OpenStreetMap infrastructure even without keys):
```ini
OPENCHARGEMAP_API_KEY=your_key_here
OPENROUTESERVICE_API_KEY=your_key_here
APP_HOST=0.0.0.0
APP_PORT=8085
```

> **Security note:** `APP_HOST` binds to `0.0.0.0` by default so the app is reachable
> from your network / preview environment. For a machine exposed to the internet,
> put it behind a reverse proxy with TLS and restrict `CORS_ORIGINS`.

### Step 3: Launch the Application
```bash
python main.py
```
Open **`http://127.0.0.1:8085`** in any web browser.

---

## 7. Security Hardening (v2.0)

The backend has been hardened against common web vulnerabilities:

| Protection | Implementation |
|---|---|
| **Restricted CORS** | Origin allowlist (no `*` wildcard); configurable via `CORS_ORIGINS` |
| **Input validation** | Strict Pydantic bounds on coordinates, station counts, costs, budget, names |
| **Request size limit** | Max 2 MB body (`MAX_REQUEST_BYTES`, 413 response) |
| **Rate limiting** | Per-IP fixed-window limits on all `/api/*` endpoints (429 response) |
| **Security headers** | `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, CSP |
| **Bounded caches** | Geocode LRU cache capped (no unbounded memory growth) |
| **Safe external queries** | Coordinates formatted with fixed precision before URL/QL interpolation |
| **No internal error leakage** | Network errors returned generically; details logged server-side only |
| **Sanitized search queries** | Length cap, control-char rejection |
| **Secret hygiene** | `.env` gitignored; `.env.example` as the template |

Tunable via environment variables (see `backend/config.py`):
`CORS_ORIGINS`, `RATE_LIMITS`, `MAX_REQUEST_BYTES`, `MAX_STATIONS_PER_REQUEST`,
`MAX_MATRIX_LOCATIONS`, `MAX_KNAPSACK_CANDIDATES`, `MAX_BUDGET`, `MAX_QUERY_LENGTH`,
`MAX_NAME_LENGTH`, `GEOCODE_CACHE_SIZE`.

Security regression tests: `tests/test_security.py` (run with the suite below).

### Step 4: Run the Complete Automated Test Suite
```bash
python -m pytest tests/test_backend_api.py tests/test_security.py tests/test_mst.py tests/test_dijkstra.py tests/test_knapsack.py tests/test_models.py -v
```

---

## 8. Deployment Guide

The application is **deployment-ready**. The recommended deployment method is **Railway** — it's the simplest path with a free tier and automatic builds from GitHub.

### 8.1 Deploy to Railway (Recommended)

1. **Push your code to GitHub** (already done if using this repo).
2. **Go to [railwayapp.com](https://railwayapp.com)** and sign up (free tier available).
3. **Click "New Project"** → "Import from GitHub" → select `Omprakash-prog03/DAA-project-and-deploy`.
4. **Railway auto-detects the `Procfile`** and starts the app automatically. No manual config needed.
5. **Wait for deployment** (~1-2 minutes). Railway shows live logs.
6. **Visit your app** at the URL Railway provides (e.g., `https://ev-charging-planner.up.railway.app`).

**Optional: Set environment variables** in Railway → Settings → Variables:

| Variable | Purpose | Default |
|---|---|---|
| `OPENCHARGEMAP_API_KEY` | Open Charge Map API key (optional) | empty (OSM fallback) |
| `OPENROUTESERVICE_API_KEY` | OpenRouteService API key (optional) | empty (OSRM fallback) |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `*` |
| `RATE_LIMITS` | Per-IP rate limits (`prefix:max:window`) | sensible defaults |

The app works without any API keys — it uses OpenStreetMap infrastructure as a fallback.

### 8.2 Deploy with Docker (local / any platform)

```bash
# Build and run
docker build -t ev-planner .
docker run -d -p 8085:8085 \
  -e OPENCHARGEMAP_API_KEY=your_key \
  -e OPENROUTESERVICE_API_KEY=your_key \
  ev-planner

# Or with docker-compose (reads .env automatically)
cp .env.example .env
docker compose up -d --build
```

### 8.3 Deploy to Other PaaS (Heroku / Render / Cloud Run)

The `Procfile` starts gunicorn with uvicorn workers automatically:

```bash
# Heroku
heroku create your-app-name
git push heroku main

# Render / Cloud Run
# Connect the repo; the app starts via the Procfile on the provided PORT.
# Set environment variables in the platform dashboard.
```

### 8.4 Deploy on a VPS (manual)

```bash
# 1. Install Python 3.11+
# 2. Clone and set up
git clone <your-repo> && cd DAA-project-and-deploy
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit keys

# 3. Start with the production script
./start.sh

# 4. (Optional) Run behind nginx with TLS
#    Proxy / to http://127.0.0.1:8085
```

### 8.5 Production Checklist

- [ ] Set `CORS_ORIGINS` to your production domain (or leave default)
- [ ] Configure `RATE_LIMITS` for your expected traffic
- [ ] Add API keys for richer data (optional)
- [ ] Put the app behind a reverse proxy (nginx/Caddy) with TLS
- [ ] Verify `/api/health` returns `{"status":"healthy"}`

---

## 9. Testing Instructions Using a Real Location (Viva Demonstration)

1. Open **`http://127.0.0.1:8085`** in your browser.
2. In the top search bar, enter **`Bhubaneswar`** (or **`Delhi`**, **`London`**, **`New York`**) and click **Search Area**.
3. Observe the real Earth map fly to the exact coordinates and load real charging stations.
4. Click on any charging station marker to view its real address, operator, and connector specifications.
5. In the left drawer, select candidate stations (e.g. 5 stations) and adjust their installation costs (₹) or benefit scores.
6. Open the **1. Kruskal MST** tab on the right and click **Run Kruskal's MST**. Notice the neon green feeder lines connecting the stations along real road distances.
7. Open the **2. Dijkstra** tab, choose an Origin and Destination station, and click **Run Dijkstra Search**. Notice the white/cyan driving path overlay showing true road distance and driving duration.
8. Open the **3. 0/1 Knapsack** tab, enter a budget (e.g., ₹5,00,000), and click **Run 0/1 Knapsack DP**. Notice the optimal stations highlighted with glowing green rings and review the exact exclusion reasons for rejected stations.
9. Click **Clear / Reset** to clear all layers and return to the clean real Earth map.
