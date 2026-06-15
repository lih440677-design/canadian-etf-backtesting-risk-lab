import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { RollingMetricPoint } from "../types/backtest";
import { formatNumber, formatPercent } from "../utils/formatters";

interface RollingMetricsChartProps {
  rollingMetrics: RollingMetricPoint[];
}

export function RollingMetricsChart({ rollingMetrics }: RollingMetricsChartProps) {
  if (rollingMetrics.length === 0) {
    return (
      <section className="panel">
        <h2 className="text-lg font-semibold text-ink">Rolling Metrics</h2>
        <div className="empty-state mt-4">Not enough portfolio history for rolling metrics.</div>
      </section>
    );
  }

  return (
    <section className="panel min-h-[360px]">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-ink">Rolling Metrics</h2>
        <p className="text-sm text-graphite">Rolling return, volatility, and Sharpe ratio</p>
      </div>
      <div className="h-[290px] w-full">
        <ResponsiveContainer>
          <LineChart data={rollingMetrics} margin={{ top: 8, right: 16, bottom: 18, left: 8 }}>
            <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              minTickGap={36}
              tick={{ fontSize: 12 }}
              label={{ value: "Date", position: "insideBottom", offset: -12 }}
            />
            <YAxis
              yAxisId="percent"
              tickFormatter={(value) => formatPercent(Number(value))}
              tick={{ fontSize: 12 }}
              width={78}
              label={{ value: "Return / Volatility", angle: -90, position: "insideLeft" }}
            />
            <YAxis
              yAxisId="ratio"
              orientation="right"
              tickFormatter={(value) => formatNumber(Number(value), 1)}
              tick={{ fontSize: 12 }}
              width={52}
            />
            <Tooltip
              formatter={(value, name) =>
                name === "Rolling Sharpe"
                  ? formatNumber(Number(value), 2)
                  : formatPercent(Number(value))
              }
              labelFormatter={(label) => `Date: ${label}`}
            />
            <Legend verticalAlign="top" height={32} />
            <Line
              yAxisId="percent"
              type="monotone"
              dataKey="rolling_return"
              name="Rolling Return"
              stroke="#0f766e"
              strokeWidth={2}
              dot={false}
              connectNulls
            />
            <Line
              yAxisId="percent"
              type="monotone"
              dataKey="rolling_volatility"
              name="Rolling Volatility"
              stroke="#b45309"
              strokeWidth={2}
              dot={false}
              connectNulls
            />
            <Line
              yAxisId="ratio"
              type="monotone"
              dataKey="rolling_sharpe"
              name="Rolling Sharpe"
              stroke="#2563eb"
              strokeWidth={2}
              dot={false}
              connectNulls
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

