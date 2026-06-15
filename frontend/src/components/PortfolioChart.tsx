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

import type { PortfolioPoint } from "../types/backtest";
import { formatCurrency } from "../utils/formatters";

interface PortfolioChartProps {
  portfolioCurve: PortfolioPoint[];
  beforeCostCurve: PortfolioPoint[];
  benchmarkCurve: PortfolioPoint[];
}

export function PortfolioChart({ portfolioCurve, beforeCostCurve, benchmarkCurve }: PortfolioChartProps) {
  const beforeCostByDate = new Map(beforeCostCurve.map((point) => [point.date, point.value]));
  const benchmarkByDate = new Map(benchmarkCurve.map((point) => [point.date, point.value]));
  const data = portfolioCurve.map((point) => ({
    date: point.date,
    afterCosts: point.value,
    beforeCosts: beforeCostByDate.get(point.date) ?? null,
    benchmark: benchmarkByDate.get(point.date) ?? null,
  }));

  return (
    <section className="panel min-h-[360px]">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-ink">Portfolio Value</h2>
          <p className="text-sm text-graphite">After costs, before costs, and buy-and-hold benchmark</p>
        </div>
      </div>
      <div className="h-[290px] w-full">
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 8, right: 18, bottom: 18, left: 8 }}>
            <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              minTickGap={36}
              tick={{ fontSize: 12 }}
              label={{ value: "Date", position: "insideBottom", offset: -12 }}
            />
            <YAxis
              tickFormatter={(value) => formatCurrency(Number(value))}
              tick={{ fontSize: 12 }}
              width={86}
              label={{ value: "Portfolio Value", angle: -90, position: "insideLeft" }}
            />
            <Tooltip
              formatter={(value) => formatCurrency(Number(value))}
              labelFormatter={(label) => `Date: ${label}`}
            />
            <Legend verticalAlign="top" height={32} />
            <Line
              type="monotone"
              dataKey="afterCosts"
              name="After Costs"
              stroke="#0f766e"
              strokeWidth={2}
              dot={false}
              connectNulls
            />
            <Line
              type="monotone"
              dataKey="beforeCosts"
              name="Before Costs"
              stroke="#2563eb"
              strokeWidth={2}
              dot={false}
              connectNulls
            />
            <Line
              type="monotone"
              dataKey="benchmark"
              name="Benchmark"
              stroke="#b45309"
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
