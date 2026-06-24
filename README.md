# Mavuno API

A FastAPI service that exposes the Mavuno Neo4j Aura graph as a REST API for
credit-readiness and farm risk profiling of smallholder farmers.

---

## Quick start

### 1. Clone / copy this project

```bash
cd mavuno-api
```

### 2. Create a virtual environment

```bash
python -m venv .veenv # you can give your own name
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Neo4j Aura credentials

```bash
cp .env.example .env
```

Edit `.env` and fill in  Aura connection string, username, and password:

```
NEO4J_URI=neo4j+s://<your-instance-id>.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your-password>
```


### 4. Run the server

```bash
python3 -m uvicorn main:app --reload
```

The API is now available at <http://localhost:8000>.
Interactive docs (Swagger UI): <http://localhost:8000/docs>

---

## Endpoint reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Service info |
| GET | `/health` | Liveness + Neo4j ping |
| **Farmers** | | |
| GET | `/farmers` | List farmers — filter by `status`, `county` |
| GET | `/farmers/{id}` | Full farmer detail |
| GET | `/farmers/{id}/farms` | Farms owned by a farmer |
| GET | `/farmers/{id}/credit-profile` | Credit score, risks, recommendations, AI run |
| GET | `/farmers/{id}/financial-profile` | Revenue, expenses, cash-flow score |
| GET | `/farmers/{id}/expenses` | Expense transactions — filter by `category` |
| GET | `/farmers/{id}/production` | Production records with sales and evidence |
| GET | `/farmers/{id}/loans` | Loan history |
| **Lenders** | | |
| GET | `/lenders` | List all lender / bank nodes |
| GET | `/lenders/{id}` | Lender detail |
| GET | `/lenders/{id}/applicants` | Farmers who applied — filter by `min_score`, `readiness_level` |
| **Groups** | | |
| GET | `/groups` | List farmer groups — filter by `group_type`, `county` |
| GET | `/groups/{id}` | Group detail |
| GET | `/groups/{id}/members` | Farmers belonging to the group |
| **Analytics** | | |
| GET | `/analytics/graph-stats` | Node and relationship counts |
| GET | `/analytics/credit-score-distribution` | Score buckets by readiness level |
| GET | `/analytics/top-risk-categories` | Most common risk categories |
| GET | `/analytics/county-summary` | Per-county farmer and credit aggregates |
| GET | `/analytics/weather-snapshots` | Recent weather and soil snapshots |
| GET | `/analytics/loan-repayment-rate` | On-time repayment rate by lender type |

---

## Project layout

```
mavuno-api/
├── app/
│   ├── main.py          # FastAPI app, lifespan, middleware
│   ├── config.py        # Pydantic settings (reads .env)
│   ├── db/
│   │   └── neo4j.py     # Async driver init, session helper
│   ├── models/
│   │   └── schemas.py   # Pydantic response models
│   └── routers/
│       ├── farmers.py   # /farmers routes
│       ├── lenders.py   # /lenders routes
│       ├── groups.py    # /groups routes
│       └── analytics.py # /analytics routes
├── requirements.txt
├── .env.example
└── README.md
```

---

## Notes

- The driver uses the **async** Neo4j Python client (`AsyncGraphDatabase`) so all
  queries run non-blocking inside FastAPI's async event loop.
- For production, we will set `APP_ENV=production` and put credentials in environment.
