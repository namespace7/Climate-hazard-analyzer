
# Climate Hazard Trend Analyzer

A full-stack application for exploring historical heatwave events and annual temperature trends for a selected geographic location and time period.

## Features

- Interactive React dashboard for selecting coordinates and date ranges.
- Historical daily maximum temperatures retrieved from the Open-Meteo Archive API.
- Heatwave detection using a temperature threshold and a minimum duration of three consecutive days.
- Annual summaries of event counts, total heatwave days, and longest events.
- Linear regression analysis of annual heatwave days.
- In-memory caching of historical weather responses.
- MongoDB persistence and caching of completed analysis results.
- FastAPI endpoints with input validation.
- Automated Python tests for analysis, API behavior, and repository logic.

## Architecture

```text
React + TypeScript + Recharts
              |
              v
        FastAPI backend
              |
              v
     MongoDB analysis cache
              |
       Cache miss?
              |
              v
      Open-Meteo Archive API
              |
              v
      Climate analysis pipeline
       |       |       |
    Threshold Events  Trend
              |
              v
       MongoDB persistence
              |
              v
        JSON response
```

## Technology stack

### Frontend

- React
- TypeScript
- Vite
- Recharts
- Lucide React

### Backend

- Python 3.11
- FastAPI
- Uvicorn
- HTTPX
- NumPy
- SciPy
- PyMongo
- python-dotenv
- pytest

### Database and data source

- MongoDB
- Open-Meteo Historical Weather API

## Prerequisites

Install the following before running the application:

- Python 3.11
- Node.js and npm compatible with the installed Vite version
- MongoDB running locally or at an accessible MongoDB URI

## Project structure

```text
climate-hazard-analyzer/
├── backend/
│   ├── config/
│   │   ├── database.py
│   │   ├── analysis_repository.py
│   │   ├── setup_database.py
│   │   └── check_database.py
│   ├── tests/
│   ├── analyze_climate.py
│   ├── climate_analysis.py
│   ├── climate_threshold.py
│   ├── climate_trend.py
│   ├── heatwave.py
│   ├── main.py
│   ├── weather_service.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Configuration

Create `backend/.env`:

```dotenv
MONGODB_URI=mongodb://root:YOUR_PASSWORD@localhost:27017/?authSource=admin
MONGODB_DATABASE=climate_hazard_analyzer
```

Replace `YOUR_PASSWORD` with the password for your MongoDB user.

Never commit `.env` or expose database credentials.

## Run the backend

From the project root:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Verify the MongoDB connection:

```bash
python -m config.check_database
```

Create the analysis index:

```bash
python -m config.setup_database
```

Start FastAPI:

```bash
python -m uvicorn main:app --reload
```

Backend URL: http://127.0.0.1:8000

Interactive API documentation: http://127.0.0.1:8000/docs

## Run the frontend

Open a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open the local URL printed by Vite, usually http://localhost:5173.

The Vite development server proxies `/api` requests to the FastAPI backend. Keep both development servers running.

## API

### GET `/`

Returns a basic backend health message.

### GET `/api/analyze`

Query parameters:

| Parameter | Type | Default |
|---|---|---|
| latitude | float | 26.12 |
| longitude | float | 85.39 |
| start_date | ISO date | 1990-01-01 |
| end_date | ISO date | 2020-12-31 |

Example:

```text
/api/analyze?latitude=26.12&longitude=85.39&start_date=1990-01-01&end_date=2020-12-31
```

The response includes the threshold, valid record count, heatwave event count, total heatwave days, annual statistics, trend metrics, and detected events.

## Analysis methodology

### Heatwave detection

The current implementation calculates the 95th percentile of valid daily maximum temperatures across the requested period and identifies runs of at least three consecutive days above that threshold.

Missing temperatures and gaps in consecutive dates should interrupt an event.

### Annual statistics

Annual summaries include:

- Number of heatwave events
- Total heatwave days
- Longest event duration

Years without detected events are represented with zero values.

### Trend analysis

Linear regression estimates the slope of annual heatwave days over time. The output includes the slope, direction, p-value, and R-squared.

A positive slope indicates an increasing fitted trend; it does not by itself establish causation or prove climate change.

**Methodology limitation:** the threshold is calculated from the selected analysis period rather than a fixed climatological baseline. Results from different periods may therefore not be directly comparable. This should be considered before interpreting the output as a scientific climate assessment.

## Caching and persistence

The application uses two caching layers:

1. An in-memory weather response cache with a one-hour TTL.
2. A MongoDB analysis cache with a 24-hour freshness window and an algorithm version.

The MongoDB `analyses` collection uses a compound unique index based on coordinates and date range to avoid duplicate analysis documents.

The in-memory cache is lost when the backend process restarts. MongoDB results persist across restarts.

## Run tests

From `backend/`, activate the virtual environment and run:

```bash
python -m pytest -q
```

The current test suite covers annual statistics, trend calculation, API validation and errors, weather caching, and analysis repository behavior.

## Frontend quality checks

From `frontend/`:

```bash
npm run lint
npm run build
```

Both commands should complete successfully before submission.

## Security and deployment notes

- Keep credentials in environment variables.
- Never commit `.env` or local virtual environments.
- Configure CORS, rate limiting, and production server settings before public deployment.
- Use a persistent MongoDB deployment for production.
- Configure frontend and backend production URLs appropriately.
- Review dependency compatibility and update packages deliberately.
- Add operational logging and monitoring before production use.

## Current limitations

- Heatwave is the currently implemented hazard type.
- The dashboard accepts coordinates rather than a geographic search or map selector.
- The threshold is period-dependent.
- The application is a prototype and has not been independently validated for scientific or public-safety decisions.
- Production deployment and security hardening must be verified separately.

## License

Add the license required by your project or assignment before distributing the repository.
```

## 2. Protect your secrets

From the project root, create or update `.gitignore`:

<CodeBlock language="gitignore" editable>
# Python
__pycache__/
*.py[cod]
.venv/
.pytest_cache/
.coverage
htmlcov/

# Secrets
.env
.env.*
!.env.example

# Frontend
node_modules/
dist/

# OS and editor files
.DS_Store
.vscode/
