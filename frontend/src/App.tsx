import { useState } from "react";
import type { FormEvent, ReactNode } from "react";

import {
  Activity,
  CalendarDays,
  ChartNoAxesCombined,
  Download,
  Flame,
  MapPin,
  RefreshCw,
  Search,
  Thermometer,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./App.css";

type AnnualStatistic = {
  year: number;
  event_count: number;
  total_heatwave_days: number;
  longest_event_days: number;
};

type HeatwaveEvent = {
  start_date: string;
  end_date: string;
  duration: number;
};

type mann_kendall = {
  s_statistic: number;
  z_statistic: number;
  kendall_tau: number;
  p_value: number;
  direction: string;
  alpha: number;
};

type AnalysisResult = {
  latitude: number;
  longitude: number;
  start_date: string;
  end_date: string;
  threshold_celsius: number;
  valid_temperature_records: number;
  heatwave_event_count: number;
  total_heatwave_days: number;
  annual_statistics: AnnualStatistic[];
  trend: {
    slope_days_per_year: number;
    direction: string;
    p_value: number;
    r_squared: number;
  };
  mann_kendall: mann_kendall;
  events: HeatwaveEvent[];
};

function escapeCsvCell(value: string | number): string {
  let text = String(value);

  // Prevent spreadsheet formula injection for text values.
  if (typeof value === "string" && /^[=+\-@\t\r]/.test(text)) {
    text = `'${text}`;
  }

  // Escape embedded quotes and quote every CSV field.
  return `"${text.replace(/"/g, '""')}"`;
}

function downloadCsv(
  filename: string,
  headers: string[],
  rows: (string | number)[][],
): void {
  const csv = [headers, ...rows]
    .map((row) => row.map(escapeCsvCell).join(","))
    .join("\r\n");

  // Include a BOM to improve UTF-8 compatibility in spreadsheet apps.
  const blob = new Blob(["\uFEFF", csv], {
    type: "text/csv;charset=utf-8;",
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();

  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function App() {
  const [latitude, setLatitude] = useState("26.12");
  const [longitude, setLongitude] = useState("85.39");
  const [startDate, setStartDate] = useState("1990-01-01");
  const [endDate, setEndDate] = useState("2020-12-31");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [trendMethod, setTrendMethod] = useState<"regression" | "mann_kendall">(
    "regression",
  );

  async function runAnalysis(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const params = new URLSearchParams({
        latitude,
        longitude,
        start_date: startDate,
        end_date: endDate,
      });

      const response = await fetch(`/api/analyze?${params.toString()}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to analyze climate data.");
      }

      setResult(data as AnalysisResult);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong while contacting the API.",
      );
    } finally {
      setLoading(false);
    }
  }

  const trend = result?.trend;
  const isIncreasing = trend?.direction === "increasing";
  const isDecreasing = trend?.direction === "decreasing";

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="ClimateScope home">
          <span className="brand-icon">
            <Activity size={22} />
          </span>
          <span>ClimateScope</span>
        </a>
        <span className="live-status">
          <span className="status-dot" /> Analysis workspace
        </span>
      </header>

      <section className="page-heading">
        <div>
          <p className="eyebrow">CLIMATE INTELLIGENCE / DASHBOARD</p>
          <h1>Climate Hazard Trend Analyzer</h1>
          <p className="subtitle">
            Explore historical heatwaves, annual patterns, and long-term trends.
          </p>
        </div>
      </section>

      <section className="workspace">
        <aside className="control-panel">
          <div className="section-heading">
            <Search size={18} />
            <h2>Analysis parameters</h2>
          </div>

          <form onSubmit={runAnalysis}>
            <label>
              Latitude
              <input
                type="number"
                step="any"
                min="-90"
                max="90"
                required
                value={latitude}
                onChange={(e) => setLatitude(e.target.value)}
              />
            </label>

            <label>
              Longitude
              <input
                type="number"
                step="any"
                min="-180"
                max="180"
                required
                value={longitude}
                onChange={(e) => setLongitude(e.target.value)}
              />
            </label>

            <div className="location-hint">
              <MapPin size={15} />
              <span>Default location: Muzaffarpur region</span>
            </div>

            <div className="form-divider" />

            <div className="section-heading">
              <CalendarDays size={18} />
              <h2>Historical period</h2>
            </div>

            <label>
              Start date
              <input
                type="date"
                required
                value={startDate}
                max={endDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </label>

            <label>
              End date
              <input
                type="date"
                required
                value={endDate}
                min={startDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </label>

            <div className="hazard-selection">
              <span className="field-label">Hazard type</span>
              <div className="hazard-option">
                <Flame size={18} />
                <span>
                  <strong>Heatwave</strong>
                  <small>Consecutive high-temperature days</small>
                </span>
                <span className="selected-mark">✓</span>
              </div>
              <p className="field-note">
                Heatwave is the currently implemented hazard type.
              </p>
            </div>

            <button className="analyze-button" type="submit" disabled={loading}>
              {loading ? (
                <>
                  <RefreshCw size={17} className="spin" /> Analyzing data...
                </>
              ) : (
                <>
                  <ChartNoAxesCombined size={17} /> Analyze climate
                </>
              )}
            </button>
          </form>
        </aside>

        <div className="results-panel">
          {!result && !loading && !error && (
            <div className="welcome-panel">
              <div className="welcome-icon">
                <Thermometer size={30} />
              </div>
              <h2>Your climate analysis starts here</h2>
              <p>
                Choose a location and historical period, then run an analysis to
                explore detected heatwaves and annual trends.
              </p>
              <button
                className="secondary-button"
                onClick={() => {
                  const form = document.querySelector("form");
                  form?.requestSubmit();
                }}
              >
                Run default analysis
              </button>
            </div>
          )}

          {loading && (
            <div className="loading-panel">
              <RefreshCw size={28} className="spin" />
              <h2>Analyzing historical climate data</h2>
              <p>
                The first request may take a little while to retrieve records.
              </p>
            </div>
          )}

          {error && (
            <div className="error-panel" role="alert">
              <strong>Analysis failed</strong>
              <p>{error}</p>
              <button className="secondary-button" onClick={() => setError("")}>
                Dismiss
              </button>
            </div>
          )}

          {result && !loading && (
            <>
              <div className="results-title">
                <div>
                  <p className="eyebrow">ANALYSIS RESULTS</p>
                  <h2>Historical heatwave overview</h2>
                  <p className="results-caption">
                    {result.start_date} — {result.end_date}
                    {" · "}
                    {result.latitude}, {result.longitude}
                  </p>
                </div>
                <span className="result-badge">Analysis complete</span>
              </div>

              <div className="metric-grid">
                <MetricCard
                  label="Heatwave events"
                  value={result.heatwave_event_count}
                  note="Detected events"
                  icon={<Flame size={19} />}
                />
                <MetricCard
                  label="Heatwave days"
                  value={result.total_heatwave_days}
                  note="Across detected events"
                  icon={<CalendarDays size={19} />}
                />
                <MetricCard
                  label="Threshold"
                  value={`${result.threshold_celsius}°C`}
                  note="95th percentile"
                  icon={<Thermometer size={19} />}
                />
                <MetricCard
                  label="Valid records"
                  value={result.valid_temperature_records.toLocaleString()}
                  note="Daily temperature records"
                  icon={<Activity size={19} />}
                />
              </div>

              <div className="export-actions">
                <div>
                  <strong>Export analysis</strong>
                  <p>Download the results for this location and period.</p>
                </div>

                <div className="export-buttons">
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                      downloadCsv(
                        `annual-heatwave-statistics-${result.start_date}-to-${result.end_date}.csv`,
                        [
                          "latitude",
                          "longitude",
                          "start_date",
                          "end_date",
                          "threshold_celsius",
                          "year",
                          "event_count",
                          "total_heatwave_days",
                          "longest_event_days",
                        ],
                        result.annual_statistics.map((item) => [
                          result.latitude,
                          result.longitude,
                          result.start_date,
                          result.end_date,
                          result.threshold_celsius,
                          item.year,
                          item.event_count,
                          item.total_heatwave_days,
                          item.longest_event_days,
                        ]),
                      )
                    }
                  >
                    <Download size={16} />
                    Annual statistics CSV
                  </button>

                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                      downloadCsv(
                        `heatwave-events-${result.start_date}-to-${result.end_date}.csv`,
                        [
                          "latitude",
                          "longitude",
                          "start_date",
                          "end_date",
                          "threshold_celsius",
                          "event_start_date",
                          "event_end_date",
                          "duration_days",
                        ],
                        result.events.map((item) => [
                          result.latitude,
                          result.longitude,
                          result.start_date,
                          result.end_date,
                          result.threshold_celsius,
                          item.start_date,
                          item.end_date,
                          item.duration,
                        ]),
                      )
                    }
                  >
                    <Download size={16} />
                    Heatwave events CSV
                  </button>
                </div>
              </div>

              <section className="content-card chart-card">
                <div className="card-heading">
                  <div>
                    <h3>Annual heatwave days</h3>
                    <p>
                      Total days belonging to detected heatwave events per year
                    </p>
                  </div>
                  <span className="chart-legend">
                    <span /> Heatwave days
                  </span>
                </div>

                <div className="chart-container">
                  {result.annual_statistics.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={result.annual_statistics}
                        margin={{ top: 12, right: 16, left: 0, bottom: 8 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis
                          dataKey="year"
                          tick={{ fontSize: 11 }}
                          minTickGap={28}
                        />
                        <YAxis
                          allowDecimals={false}
                          tick={{ fontSize: 11 }}
                          width={38}
                        />
                        <Tooltip
                          formatter={(value) => [
                            `${value} days`,
                            "Heatwave days",
                          ]}
                          labelFormatter={(label) => `Year ${label}`}
                        />
                        <Line
                          type="monotone"
                          dataKey="total_heatwave_days"
                          stroke="#e66b42"
                          strokeWidth={2.5}
                          dot={false}
                          activeDot={{ r: 5 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="empty-chart">
                      No annual statistics available.
                    </p>
                  )}
                </div>
              </section>

              <section className="content-card trend-card">
                <div className="card-heading trend-card-heading">
                  <div>
                    <h3>Long-term trend analysis</h3>
                    <p>
                      Compare two statistical methods for annual heatwave days
                    </p>
                  </div>
                  {trendMethod === "regression" ? (
                    isIncreasing ? (
                      <TrendingUp size={24} className="trend-up" />
                    ) : isDecreasing ? (
                      <TrendingDown size={24} className="trend-down" />
                    ) : (
                      <Activity size={24} />
                    )
                  ) : (
                    <Activity size={24} />
                  )}
                </div>

                <div
                  className="trend-toggle"
                  role="group"
                  aria-label="Select trend analysis method"
                >
                  <button
                    type="button"
                    className={`trend-toggle-button ${
                      trendMethod === "regression" ? "active" : ""
                    }`}
                    aria-pressed={trendMethod === "regression"}
                    onClick={() => setTrendMethod("regression")}
                  >
                    Linear Regression
                  </button>
                  <button
                    type="button"
                    className={`trend-toggle-button ${
                      trendMethod === "mann_kendall" ? "active" : ""
                    }`}
                    aria-pressed={trendMethod === "mann_kendall"}
                    onClick={() => setTrendMethod("mann_kendall")}
                  >
                    Mann–Kendall
                  </button>
                </div>

                {trendMethod === "regression" ? (
                  <>
                    <div className="trend-grid">
                      <div>
                        <span className="metric-label">Direction</span>
                        <strong className="trend-value">
                          {trend?.direction.replace("_", " ") ?? "Unavailable"}
                        </strong>
                      </div>
                      <div>
                        <span className="metric-label">Slope</span>
                        <strong className="trend-value">
                          {trend?.slope_days_per_year ?? "—"}
                        </strong>
                        <small>days / year</small>
                      </div>
                      <div>
                        <span className="metric-label">P-value</span>
                        <strong className="trend-value">
                          {trend?.p_value ?? "—"}
                        </strong>
                        <small>
                          {trend
                            ? trend.p_value < 0.05
                              ? "Statistically significant"
                              : "Not significant at 0.05"
                            : "Unavailable"}
                        </small>
                      </div>
                      <div>
                        <span className="metric-label">R²</span>
                        <strong className="trend-value">
                          {trend?.r_squared ?? "—"}
                        </strong>
                      </div>
                    </div>

                    <p className="method-note">
                      Linear regression estimates the rate of change in annual
                      heatwave days. Interpret the slope alongside the p-value
                      and R².
                    </p>
                  </>
                ) : (
                  <>
                    <div className="trend-grid">
                      <div>
                        <span className="metric-label">Test conclusion</span>
                        <strong className="trend-value">
                          {result.mann_kendall.direction.replace(/_/g, " ")}
                        </strong>
                      </div>
                      <div>
                        <span className="metric-label">Kendall's tau</span>
                        <strong className="trend-value">
                          {result.mann_kendall.kendall_tau.toFixed(4)}
                        </strong>
                        <small>Monotonic association</small>
                      </div>
                      <div>
                        <span className="metric-label">P-value</span>
                        <strong className="trend-value">
                          {result.mann_kendall.p_value.toFixed(4)}
                        </strong>
                        <small>
                          {result.mann_kendall.p_value <
                          result.mann_kendall.alpha
                            ? "Statistically significant"
                            : `Not significant at ${result.mann_kendall.alpha}`}
                        </small>
                      </div>
                      <div>
                        <span className="metric-label">Z statistic</span>
                        <strong className="trend-value">
                          {result.mann_kendall.z_statistic.toFixed(3)}
                        </strong>
                        <small>S: {result.mann_kendall.s_statistic}</small>
                      </div>
                    </div>

                    <p className="method-note">
                      The Mann–Kendall test checks for a monotonic trend without
                      assuming a linear relationship. A p-value at or above the
                      significance threshold means the test did not find
                      sufficient evidence of a trend; it does not prove that no
                      trend exists.
                    </p>
                  </>
                )}
              </section>

              <section className="content-card events-card">
                <div className="card-heading">
                  <div>
                    <h3>Detected heatwave events</h3>
                    <p>
                      Events are identified using the backend threshold and
                      duration rule.
                    </p>
                  </div>
                  <span className="event-count">
                    {result.events.length} events
                  </span>
                </div>

                <div className="table-wrapper">
                  <table>
                    <thead>
                      <tr>
                        <th>Start date</th>
                        <th>End date</th>
                        <th>Duration</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.events.slice(0, 20).map((item, index) => (
                        <tr key={`${item.start_date}-${index}`}>
                          <td>{item.start_date}</td>
                          <td>{item.end_date}</td>
                          <td>
                            <span className="duration-pill">
                              {item.duration} days
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {result.events.length > 20 && (
                  <p className="table-footnote">
                    Showing the first 20 of {result.events.length} events.
                  </p>
                )}
                {result.events.length === 0 && (
                  <p className="empty-chart">
                    No heatwave events detected for this period.
                  </p>
                )}
              </section>
            </>
          )}
        </div>
      </section>

      <footer className="footer">
        <span>ClimateScope · Climate Hazard Trend Analyzer</span>
        <span>Historical data powered by Open-Meteo</span>
      </footer>
    </main>
  );
}

function MetricCard({
  label,
  value,
  note,
  icon,
}: {
  label: string;
  value: string | number;
  note: string;
  icon: ReactNode;
}) {
  return (
    <div className="metric-card">
      <div className="metric-top">
        <span className="metric-label">{label}</span>
        <span className="metric-icon">{icon}</span>
      </div>
      <strong className="metric-value">{value}</strong>
      <span className="metric-note">{note}</span>
    </div>
  );
}

export default App;
