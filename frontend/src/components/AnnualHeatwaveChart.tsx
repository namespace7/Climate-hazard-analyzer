import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export type AnnualStatistic = {
  year: number;
  event_count: number;
  total_heatwave_days: number;
  longest_event_days: number;
};

type AnnualHeatwaveChartProps = {
  data: AnnualStatistic[];
};

export default function AnnualHeatwaveChart({
  data,
}: AnnualHeatwaveChartProps) {
  if (data.length === 0) {
    return <p className="empty-chart">No annual statistics available.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart
        data={data}
        margin={{ top: 12, right: 16, left: 0, bottom: 8 }}
      >
        <CartesianGrid strokeDasharray="3 3" vertical={false} />

        <XAxis dataKey="year" tick={{ fontSize: 11 }} minTickGap={28} />

        <YAxis allowDecimals={false} tick={{ fontSize: 11 }} width={38} />

        <Tooltip
          formatter={(value) => [`${value} days`, "Heatwave days"]}
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
  );
}
