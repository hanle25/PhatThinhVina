# Truck Load Planner — Phat Thinh Vina

An order-to-truck optimization tool I built and shipped during my 2025 internship at Phat Thinh Vina, a B2B distributor in Ho Chi Minh City. It replaced a manual dispatch process and cut truck assignment time by **70%** ([X] → [Y] minutes per day of dispatcher time).

## The problem

Every day, dispatch staff had to fit ~10 B2B orders (800 kg – 4 tons each) onto a fleet of 2–3 trucks by hand. Each assignment had to respect truck capacity, product weight and volume, which storage site the goods ship from, and company rules about which loads can share a truck. Doing this in spreadsheets was slow and error-prone.

## What it does

Staff enter the day's orders in a React form. The Flask back end returns a truck plan: which truck carries which orders, from which storage site, and how full each truck is.

1. **Effective space.** Each product line is converted to a kg-equivalent load: `quantity × (unit weight × space factor + offset)`, with the space factor per product catalog stored in the database. This captures bulky-but-light items that weight alone misses.
2. **Storage selection.** When an order can ship from several storage sites, the nearest one to the customer is chosen by haversine distance.
3. **Bin packing.** Large lines are split by quantity so no piece exceeds the largest truck, then orders are packed with **First-Fit Decreasing** across truck sizes from 1.5 t to 15 t.
4. **Business rules.**
   - A 15-ton truck may only serve a single customer.
   - Contract vehicles are used before hired vehicles.
   - Storage-to-storage transfers ride along on customer trucks when there is spare capacity.
   - Off-route detection: a stop joins another customer's truck only if the detour stays within 25% of the direct route.

## Architecture

```
React (frontend/)  ──REST──▶  Flask API (backend/routes.py)  ──SQLAlchemy──▶  PostgreSQL (Neon)
  order entry,                  /customers  /storages                      customers, vehicles,
  assignment results            /catalogs   /assign_trucks                 storages, catalogs
```

Schema changes are managed with Flask-Migrate (Alembic) in `backend/migrations/`.

## Run it locally

```bash
# 1. Configure
cp .env.example backend/.env          # fill in DATABASE_URL
# (frontend variables from .env.example go in frontend/.env)

# 2. Back end
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
flask run                             # http://localhost:5000

# 3. Front end (new terminal)
cd frontend
npm install
npm start                             # http://localhost:3000
```

Windows and server deployment notes: [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md), [WINDOWS_DEPLOYMENT_INSTRUCTIONS.md](WINDOWS_DEPLOYMENT_INSTRUCTIONS.md).

## Results

| | Before | After |
|---|---|---|
| Time to assign the day's orders | [X] min | [Y] min |
| Orders per day | ~10 | ~10 |
| Fleet | 2–3 trucks | 2–3 trucks |

## Limitations and next steps

- First-Fit Decreasing is a heuristic. At this scale it is fast and close to optimal, but an exact solver (OR-Tools CP-SAT) could guarantee the minimum number of trucks.
- Routing uses straight-line distance, not road distance.
- `routes.py` holds both the algorithms and the API; splitting the optimizer into its own module with unit tests is the next refactor.

## Tech

Python, Flask, SQLAlchemy, Flask-Migrate, PostgreSQL (Neon), React
