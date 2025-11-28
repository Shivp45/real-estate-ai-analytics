import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ResponsiveContainer
} from "recharts";

const colors = ["#0d6efd", "#198754", "#dc3545", "#fd7e14", "#6f42c1"];

const ChartView = ({ chart }) => {
  // Safety checks — prevent crashes
  if (!chart || typeof chart !== "object") return null;
  if (!chart.series || !Array.isArray(chart.series) || chart.series.length === 0) {
    return null;
  }

  // Ensure yKeys exists, otherwise fallback to first available numeric key.
  const xKey = chart.xKey || "Year";
  const yKey =
    chart.yKeys?.[0] ||
    Object.keys(chart.series?.[0]?.data?.[0] || {}).find(
      (k) => k !== xKey && typeof chart.series[0].data[0][k] === "number"
    );

  if (!yKey) return null; // still no usable numeric column → skip

  // Format dataset safely
  const allPoints = {};
  try {
    chart.series.forEach((series) => {
      if (!series.data) return;

      series.data.forEach((point) => {
        const xVal = point[xKey];
        if (xVal === undefined || xVal === null) return;

        if (!allPoints[xVal]) {
          allPoints[xVal] = { [xKey]: xVal };
        }

        // Avoid junk data
        const value = point[yKey];
        allPoints[xVal][`${series.name}_${yKey}`] =
          typeof value === "number" ? value : null;
      });
    });
  } catch {
    return null;
  }

  const data = Object.values(allPoints).sort((a, b) => a[xKey] - b[xKey]);

  return (
    <div className="mt-3">
      <h6 className="fw-semibold">{chart.title ?? "Chart"}</h6>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xKey} />
          <YAxis />
          <Tooltip />
          <Legend />
          {chart.series.map((series, idx) => (
            <Line
              key={series.name}
              type="monotone"
              dataKey={`${series.name}_${yKey}`}
              name={`${series.name} ${yKey}`}
              stroke={colors[idx % colors.length]}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ChartView;
