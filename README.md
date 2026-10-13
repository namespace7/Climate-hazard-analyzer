
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
- Automated Python tests for analysis, API behavior, repository logic, climate logic, API behavior, caching, and trend analysis.
- Interactive Leaflet map for selecting geographic coordinates.
- CSV exports for annual heatwave statistics and individual heatwave events.
- Mann-Kendall non-parametric trend testing alongside linear regression.
- API rate limiting and input validation.


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
    Threshold Events Linear Regression Mann-Kendall
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
- Leaflet
- React Leaflet

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


## Trend analysis

The application provides two complementary methods for analyzing annual
heatwave days.

### Linear regression

Linear regression estimates the relationship between year and annual
heatwave days.

The output includes:

- Slope, expressed in heatwave days per year.
- Estimated trend direction.
- P-value.
- R-squared (R²), measuring the proportion of variation explained by
  the fitted linear relationship.

A positive slope indicates an increasing fitted trend; a negative slope
indicates a decreasing fitted trend. Statistical significance must be
evaluated separately from the slope.

### Mann-Kendall test

The Mann-Kendall test evaluates whether observations exhibit a monotonic
trend without assuming that the relationship with time is linear.

The output includes:

- Kendall's tau, indicating the direction and strength of the
  monotonic association.
- S statistic, based on pairwise comparisons of observations.
- Z statistic, the standardized test statistic.
- P-value and trend conclusion.

The application uses a significance level of 0.05. A p-value below
this threshold provides evidence against the null hypothesis of no
monotonic trend, subject to the test's assumptions.

A non-significant result means that the test did not find sufficient
evidence of a trend. It does not prove that no trend exists.

### Interpretation and limitations

The methods may produce different p-values because they test different
types of relationships.

The current Mann-Kendall implementation uses a normal approximation
with a continuity correction and tie-adjusted variance. Short time
series and serial correlation can affect the reliability of the result.

Neither method establishes causation.

The application calculates its temperature threshold from the selected
analysis period rather than a fixed climatological baseline. Results
from different periods may therefore not be directly comparable.
A fixed historical baseline and additional checks for serial correlation
would improve the scientific robustness of the analysis.


## Interactive map

The frontend includes a Leaflet map using OpenStreetMap tiles.

Users can select a location by clicking the map or enter latitude and
longitude manually. The selected coordinates are displayed in the
analysis form and are used when the user runs the analysis.

The application validates coordinate ranges before submitting an
analysis request. Map tiles require an internet connection.

Map data and tiles are provided by OpenStreetMap contributors.

## CSV exports

The dashboard provides two CSV exports:

1. Annual statistics, including annual heatwave summaries and trend-related
   data available in the analysis response.
2. Heatwave events, including the detected event details.

The exports include location and analysis-period metadata. CSV fields are
escaped, and formula-like values are guarded against spreadsheet formula
injection.

The exports represent the current analysis response; they do not independently
recalculate the climate analysis.


## AI tools used

ChatGPT was used as a development assistant to help plan implementation
steps, explain Python and statistical concepts, review error messages,
suggest debugging approaches, and improve documentation.

The implementation was tested locally using frontend lint/build checks
and the Python test suite. The developer remains responsible for reviewing,
understanding, and validating the submitted code.


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
- Location selection supports map clicks and manual latitude/longitude entry; city-name search and bounding-box region selection are not implemented.
- The threshold is period-dependent.
- The application is a prototype and has not been independently validated for scientific or public-safety decisions.
- Production deployment and security hardening must be verified separately.

## License

Add the license required by your project or assignment before distributing the repository.

