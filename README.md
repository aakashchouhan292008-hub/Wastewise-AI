# WasteWise AI

**Predict Better. Prepare Smarter. Waste Less.**

An AI-Powered Food Waste Management System for College Canteens, built as a B.Tech CSE (Data Science) academic project at **JECRC University**.

---

## Overview

College canteens face daily demand uncertainty caused by fluctuating student attendance, weekday preferences, campus events, and holidays. Over-preparation leads to food and financial waste, while under-preparation causes shortages.

WasteWise AI addresses this with a **6-step operational workflow**:

1. **Attendance** — Capture expected campus headcount.
2. **Context** — Incorporate menu item, day of the week, holidays, and special campus events.
3. **Forecast** — Estimate demand using a trained **Random Forest Regressor** (built on pre-preparation inputs only, with zero data leakage).
4. **Prep Target** — Recommend preparation quantities with a configurable safety buffer.
5. **Daily Logs** — Record actual prepared, sold, and leftover quantities in SQLite.
6. **Feedback** — Append completed operational logs to the historical dataset and retrain the model once sufficient new records are collected.

> **Demonstration Data Notice:** The initial 1,250 historical records are clearly labeled `SYNTHETIC DEMONSTRATION DATA – NOT REAL CANTEEN RECORDS.`

---

## Technology Stack

- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Radix/Shadcn-style UI components, Lucide Icons, Recharts
- **Backend:** Python, FastAPI, Pydantic, Uvicorn
- **Machine Learning:** Pandas, NumPy, Scikit-learn (`RandomForestRegressor` + `ColumnTransformer` + `OneHotEncoder`), Joblib
- **Database:** SQLite (`backend/data/wastewise.db`) organized behind an abstract `DatabaseRepository` interface (`backend/app/database/base.py`) so Supabase (`backend/app/database/supabase_adapter.py`) can be plugged in later without rewriting routes.

---

## Project Structure

```text
wastewise-ai/
├── .env.example
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── database/
│   │   │   ├── base.py               # Repository abstraction (Supabase-ready)
│   │   │   ├── sqlite_db.py          # Active SQLite implementation
│   │   │   ├── supabase_adapter.py   # Planned Supabase integration stub
│   │   │   └── init_db.py            # Standalone DB initialization script
│   │   ├── ml/
│   │   │   ├── dataset_generator.py  # Generates 1,250 synthetic canteen records
│   │   │   ├── train_model.py        # Chronological 80/20 Random Forest training & evaluation
│   │   │   └── predictor.py          # Loads saved model & generates demand forecast
│   │   ├── models/
│   │   │   └── schemas.py            # Pydantic request validation schemas
│   │   └── routes/
│   │       ├── dashboard.py          # Module 1: Dashboard KPIs & charts
│   │       ├── predictions.py        # Module 2: AI Demand Prediction
│   │       ├── preparation.py        # Module 3: Smart Preparation
│   │       ├── waste.py              # Module 4: Food Waste Tracking CRUD
│   │       ├── inventory.py          # Module 5: Inventory & Low-Stock Alerts CRUD
│   │       ├── analytics.py          # Module 6: Analytics & CSV Export
│   │       └── system.py             # Model status, retraining & demo reset
│   └── tests/
│       └── test_api_and_ml.py
└── frontend/
    ├── package.json
    ├── tailwind.config.js
    ├── vite.config.ts
    └── src/
        ├── components/               # Layout, Logo, ToastProvider, UI controls
        ├── pages/                    # All 6 application modules
        ├── services/api.ts           # Typed REST API client
        └── types/index.ts
```

---

## Windows 11 Setup & Startup Instructions

### Prerequisites
- **Python 3.10+** (tested on Python 3.14)
- **Node.js LTS** (includes `npm`)

### 1. Backend Setup

Open PowerShell in `wastewise-ai\backend`:

```powershell
cd "D:\Antigravity Projects\wastewise-ai\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Initialize the database, generate the synthetic dataset, and train the Random Forest model:

```powershell
python -m app.database.init_db
python -m app.ml.train_model
```

Start the FastAPI backend server:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API will run at `http://127.0.0.1:8000` (interactive Swagger docs at `http://127.0.0.1:8000/docs`).

### 2. Frontend Setup

Open a second PowerShell window in `wastewise-ai\frontend`:

```powershell
cd "D:\Antigravity Projects\wastewise-ai\frontend"
npm install
npm run dev
```

Open **`http://127.0.0.1:5173`** in your browser.

---

## Running Automated Tests

From `wastewise-ai\backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

From `wastewise-ai\frontend`:

```powershell
npm run build
```

---

## Machine Learning Notes (Zero Data Leakage)

- **Input Features (known strictly before cooking):** `food_item`, `day_of_week`, `expected_attendance`, `special_event`, `holiday`, `previous_sales` (lag-1 sold portions), `is_weekend`.
- **Target Variable:** `sold_quantity`.
- **Chronological Split:** Records are sorted ascending by `record_date` (earliest 80% training, most recent 20% testing) without shuffling.
- **Evaluation:** Real held-out **MAE** and **RMSE** are calculated after every training run and displayed in the UI.
- **Safeguard:** If fewer than 50 records exist, predictions are refused with a clear insufficient-data warning rather than fabricated.

---

## Deployment Preparation Notes

- **Database Persistence:** Mount a persistent disk/volume to `backend/data/` (for `wastewise.db`) or configure `SQLITE_DB_PATH` to a persistent path. For multi-instance cloud hosting, implement `SupabaseDatabaseAdapter` (`backend/app/database/supabase_adapter.py`).
- **ML Artifacts Persistence:** Persist `backend/artifacts/demand_rf_model.joblib` and `model_metadata.json` alongside the database, or allow startup lifespan to retrain from the database on boot.
- **CORS & Frontend API URL:** Set `CORS_ORIGINS` in backend `.env` to your production frontend origin, and set `VITE_API_BASE_URL` when building the frontend if hosted on a separate domain.
- **Windows PowerShell Note:** If `npm` is blocked by PowerShell script execution policy, run `npm.cmd install` and `npm.cmd run dev`.

---

## College Presentation Demonstration Guide (5-Minute Live Flow)

1. **Dashboard Overview (`#dashboard`):** Show the 3D Sustainability Globe, the 1,250-record synthetic demo banner, KPI cards, daily/weekly charts, and Low-Stock Ingredients panel.
2. **Inventory & Menu (`#inventory`):** Show low-stock alerts, inspect the 3D stock canisters, and add a new menu item (e.g., *Aloo Paratha*) or update an ingredient's stock.
3. **AI Demand Prediction (`#prediction`):** Select *Veg Biryani*, enter `200` attendance (or `1,100` with Special Event = Yes), click **Predict Demand**, and point out the Random Forest output, Comparison Chart, `MAE`, `RMSE`, `R²`, and zero-data-leakage feature list.
4. **Smart Preparation (`#preparation`):** Click **Confirm Preparation Plan (Step 4)** from Prediction, inspect available stock and additional quantity needed, and record actual portions sold (Step 5).
5. **Food Waste Tracking (`#waste`):** Log a waste entry to show automatic calculation of `Leftover`, `Waste %`, and `Estimated Cost`, then verify the Dashboard & Analytics update immediately.
6. **Analytics & CSV Export (`#analytics`):** Filter by date/food item and click **Export CSV Report**.
7. **WasteWise Assistant (bottom-right):** Open the chatbot and ask:
   - *"Give me today's dashboard summary."*
   - *"Predict demand for Veg Biryani with 200 attendance."*
   - *"Which food items are low in stock?"*
   - *"What are the MAE, RMSE and R² values?"*
8. **Demo Reset:** Click **Reset Demo Data** in the sidebar to restore the clean 1,250-record baseline before the next evaluator.
