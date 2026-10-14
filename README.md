# Climate Hazard Trend Analyzer

A full-stack application for exploring historical heatwave events and annual temperature trends for a selected geographic point and time period.

## Features

- Interactive React dashboard with manual latitude/longitude inputs and map-based point selection.
- Date-range selection with Heatwave as the currently implemented hazard type.
- Historical daily maximum temperatures retrieved from the Open-Meteo Archive API in Celsius.
- Heatwave detection using a 95th-percentile threshold and a minimum duration of three consecutive days.
- Annual summaries for event counts, total heatwave days, and longest event duration.
- Linear regression and Mann–Kendall trend statistics for annual heatwave days.
- In-memory caching of weather API responses and MongoDB persistence/caching of completed analyses.
- FastAPI endpoints with input validation, error handling, and rate limiting.
- Interactive Leaflet map for selecting coordinates.
- CSV exports for annual statistics and individual heatwave events.
- Automated backend tests.

## Architecture

```text
React + TypeScript + Recharts + Leaflet
                   |
                   v
             Nginx (HTTP/HTTPS)
                   |
          /api/*    | static frontend
             |     |
             v     v
       FastAPI/Uvicorn   Built Vite files
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
       |        |        |
   Threshold  Events  Trend statistics
             |
             v
       MongoDB persistence
```

## Technology stack

### Frontend

- React and TypeScript
- Vite
- Recharts
- Lucide React
- Leaflet and React Leaflet

### Backend

- Python 3.11
- FastAPI and Uvicorn
- HTTPX
- NumPy and SciPy
- PyMongo
- python-dotenv
- pytest

### Database and data source

- MongoDB
- Open-Meteo Historical Weather API

## Prerequisites

- Python 3.11
- Node.js compatible with the installed Vite version (Node 22.12+ is supported by this setup)
- MongoDB running locally or reachable through a MongoDB URI

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
│   ├── climate_threshold.py
│   ├── climate_trend.py
│   ├── climate_mann_kendall.py
│   ├── heatwave.py
│   ├── main.py
│   ├── weather_service.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
└── scripts/
    ├── setup-ec2.sh
    └── deploy-ec2.sh
```

## Configuration

For local development, copy the example environment file and replace its placeholders:

```bash
cp backend/.env.example backend/.env
```

The backend reads `MONGODB_URI` and `MONGODB_DATABASE` from the environment. The MongoDB account in the URI must have `readWrite` permission on the configured application database.

Example URI format:

```text
mongodb://USERNAME:URL_ENCODED_PASSWORD@127.0.0.1:27017/climate_hazard_analyzer?authSource=climate_hazard_analyzer
```

URL-encode a password if it contains reserved URI characters. Never commit `backend/.env`, production credentials, administrator credentials, or private keys. The example file contains placeholders only.

On the EC2 deployment, systemd loads application configuration from `/etc/climate-hazard-analyzer/backend.env`. The deployment script reads a separate `MONGODB_TEST_URI` from that protected file and uses it for backend tests against `climate_hazard_analyzer_test`. Production and test database users should have access only to their respective databases.

## Run the backend

From the project root:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Configure `backend/.env`, then verify the MongoDB connection:

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

Backend URL: `http://127.0.0.1:8000`

Interactive API documentation: `http://127.0.0.1:8000/docs`

## Run the frontend

Open a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`. The Vite development server proxies `/api` requests to FastAPI. Keep both development servers running.

## API

### `GET /`

Returns a basic backend health message.

### `GET /api/analyze`

Query parameters:

| Parameter | Type | Default |
|---|---|---|
| `latitude` | float | `26.12` |
| `longitude` | float | `85.39` |
| `start_date` | ISO date | `1990-01-01` |
| `end_date` | ISO date | `2020-12-31` |

Example:

```text
/api/analyze?latitude=26.12&longitude=85.39&start_date=1990-01-01&end_date=2020-12-31
```

The response includes the threshold, valid record count, heatwave event count, total heatwave days, annual statistics, trend metrics, and detected events.

## Analysis methodology

### Heatwave detection

The current implementation calculates the 95th percentile of valid daily maximum temperatures across the requested period and identifies runs of at least three consecutive days above that threshold. Temperatures are requested from Open-Meteo in Celsius.

Missing temperatures and gaps in consecutive dates interrupt an event. This is a simple, transparent case-study definition rather than a universal climate standard.

### Annual statistics

Annual summaries include:

- Number of heatwave events
- Total heatwave days
- Longest event duration

Years without detected events are represented with zero values. Each detected event is assigned to the calendar year in which it starts.

## Trend analysis

The application provides two complementary methods for analyzing annual heatwave days.

### Linear regression

Linear regression estimates the relationship between year and annual heatwave days. The output includes slope in heatwave days per year, trend direction, p-value, and R-squared (`R²`). A positive slope indicates an increasing fitted trend; a negative slope indicates a decreasing fitted trend. Statistical significance should be evaluated separately from the slope.

### Mann–Kendall test

The Mann–Kendall test evaluates whether observations exhibit a monotonic trend without assuming a linear relationship. The output includes Kendall's tau, S statistic, Z statistic, p-value, and trend conclusion. The implementation uses significance level `0.05`, a normal approximation, continuity correction, and tie-adjusted variance.

A non-significant result means the test did not find sufficient evidence of a trend; it does not prove that no trend exists. Short time series and serial correlation can affect reliability. Neither method establishes causation.

## Interactive map

The frontend includes a Leaflet map using OpenStreetMap tiles. Users can select a point by clicking the map or enter latitude and longitude manually. The selected coordinates are displayed in the form and used for the analysis request. Map tiles require an internet connection. Map data and tiles are provided by OpenStreetMap contributors.

## CSV exports

The dashboard provides two CSV exports:

1. Annual statistics, including annual heatwave summaries.
2. Heatwave events, including event start date, end date, and duration.

Exports include location and analysis-period metadata. CSV fields are escaped, and formula-like values are guarded against spreadsheet formula injection. Exports represent the current analysis response; they do not independently recalculate the analysis.

## Caching and persistence

The application uses two caching layers:

1. An in-memory weather-response cache with a one-hour time-to-live (TTL). It is local to the API process and is lost when that process restarts.
2. A MongoDB analysis cache with a 24-hour freshness window and an algorithm version. MongoDB results persist across process restarts.

The MongoDB `analyses` collection uses a compound unique index based on coordinates and date range to avoid duplicate analysis documents.

## Security and performance

- FastAPI validates coordinate and date inputs and applies a process-local in-memory rate limit of 30 requests per client per 60 seconds.
- The rate limiter stores request timestamps in a bounded in-memory structure. Its state resets on process restart and is not shared across multiple workers or instances.
- Outbound weather API requests use a 30-second HTTP timeout and handle HTTP errors.
- CSV output guards against spreadsheet formula injection.
- Production deployment uses a root-owned environment directory, separate production/test database users, MongoDB authorization, and localhost-only bindings for MongoDB and FastAPI. Nginx serves the frontend and proxies API calls.

## Testing and quality checks

From `backend/` with the virtual environment activated:

```bash
python -m pytest -q
```

The test suite covers annual statistics, trend calculations, API validation and error paths, weather caching, and analysis repository behavior. The EC2 deployment run completed with **26 tests passing**.

From `frontend/`:

```bash
npm run lint
npm run build
```

Both commands passed during the EC2 deployment.

## Deployment

The case-study demo is hosted on an Amazon Linux 2023 EC2 instance:

- **Frontend:** Vite production build served by Nginx.
- **API:** FastAPI/Uvicorn managed by systemd and bound to `127.0.0.1:8000`; Nginx proxies `/api/` requests to it.
- **Database:** MongoDB 8.0 with authorization enabled and bound to `127.0.0.1:27017`.
- **TLS:** Let's Encrypt certificate managed by Certbot; HTTP redirects to HTTPS.
- **Renewal:** The Certbot systemd timer is enabled on the provisioned instance, and a renewal dry run succeeded.

The live-demo address is supplied separately in the case-study submission form and is intentionally not listed in this public README.

### One-time EC2 provisioning

`scripts/setup-ec2.sh` prepares the runtime, MongoDB, Nginx, application directories, and the FastAPI systemd unit. It also installs Certbot and its Nginx plugin. It is intended for initial provisioning, **not routine deployments**. Review the script before using it on a new instance, and do not rerun it on a provisioned server merely to deploy code updates.

On a new instance, configure the hostname in Nginx and DNS, create database users, and populate root-owned environment files without committing credentials. After DNS resolves to the server and inbound HTTP/HTTPS rules are in place, obtain a certificate:

```bash
sudo certbot --nginx -d YOUR_DEPLOYMENT_HOSTNAME
sudo systemctl enable --now certbot-renew.timer
sudo certbot renew --dry-run
```

Replace `YOUR_DEPLOYMENT_HOSTNAME` with the hostname configured in DNS. Do not store private keys or certificate files in the repository.

### Routine deployment

After pushing a tested change to `main`, connect to EC2 as the deployment user and run:

```bash
cd /opt/climate-hazard-analyzer
./scripts/deploy-ec2.sh
```

The deployment script fetches the latest `main` commit, requires a fast-forward update and a clean worktree, installs backend dependencies, runs backend tests with the dedicated test URI, runs frontend lint/build checks, publishes a versioned frontend release, restarts FastAPI, and checks API health.

It attempts rollback if the backend restart or health check fails. A dependency, test, or build failure before restart is not a full automatic rollback; review the deployment log and repository state before retrying.

## Current limitations

- Heatwave is the only implemented hazard type.
- Region selection is point-based: users click the map or enter latitude/longitude. City/state search and custom latitude/longitude bounding boxes are not implemented.
- The app plots annual heatwave days and displays event counts, durations, threshold, valid records, and trend statistics. It does not yet generate a percentage-change insight sentence or a separate annual event-count chart.
- The 95th-percentile threshold is calculated from the selected analysis period instead of a fixed climatological baseline. Results across different periods may therefore not be directly comparable.
- Missing temperatures and date gaps interrupt an event. The current pipeline does not implement dedicated statistical outlier screening or data-quality flags.
- The Mann–Kendall calculation uses a normal approximation with continuity correction and tie-adjusted variance. Short series and serial correlation can affect inference.
- The weather-response cache is process-local and does not have a persistent shared cache backend. Additional eviction policies and observability would improve resource predictability under many distinct queries.
- This prototype is not independently validated for scientific or public-safety decisions.
- Automated database backups, restore drills, external monitoring/alerting, and multi-instance resilience are not configured for the demo deployment.

## What I would improve with more time

1. Add data-quality diagnostics for suspicious outliers, missing-day coverage, and source metadata, with visible warnings rather than silently treating all numeric observations as equally reliable.
2. Use a fixed climatological reference period and document alternative heatwave definitions to improve comparability across locations and periods.
3. Add city/state lookup and custom region-box aggregation, an annual event-frequency chart, and carefully qualified summary insights.
4. Bound and instrument the weather cache, improve external API retry/backoff behavior, and move rate limiting to shared storage if the service scales beyond one process or instance.
5. Add automated database backups and restore testing, monitoring/alerts, and end-to-end deployment smoke tests for frontend and API.

## AI tools used

ChatGPT was used as a development assistant to help plan implementation steps, explain Python and statistical concepts, review error messages, suggest debugging approaches, and improve documentation. The implementation was tested locally with the backend test suite and frontend lint/build checks; the EC2 deployment also completed successfully with 26 backend tests passing. The developer remains responsible for reviewing, understanding, and validating the implementation and will walk through the code and make changes during the interview if shortlisted.

## License

Add the license required by your project or assignment before distributing the repository.
