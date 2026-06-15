import { AlertCircle } from "lucide-react";

import { BacktestForm } from "../components/BacktestForm";
import { Disclaimer } from "../components/Disclaimer";
import type { BacktestRequest, BacktestResponse } from "../types/backtest";
import { ResultsDashboard } from "./ResultsDashboard";

interface BacktestLabProps {
  result: BacktestResponse | null;
  loading: boolean;
  error: string | null;
  onRun: (request: BacktestRequest) => void;
}

export function BacktestLab({ result, loading, error, onRun }: BacktestLabProps) {
  return (
    <div className="space-y-6">
      <Disclaimer />
      <div className="grid grid-cols-[minmax(0,1fr)] gap-6 xl:grid-cols-[420px_minmax(0,1fr)]">
        <BacktestForm loading={loading} onRun={onRun} />
        <div className="min-w-0 space-y-6">
          {error && (
            <div className="flex items-start gap-3 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-wine">
              <AlertCircle size={18} className="mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}
          {loading && (
            <div className="panel">
              <div className="loading-bar" />
              <p className="mt-4 text-sm text-graphite">Fetching market data and running the backtest.</p>
            </div>
          )}
          {!loading && !result && !error && (
            <div className="panel min-h-[320px]">
              <h2 className="text-lg font-semibold text-ink">Results Dashboard</h2>
              <div className="empty-state mt-6">Run a backtest to populate charts, metrics, and trades.</div>
            </div>
          )}
          {result && <ResultsDashboard result={result} />}
        </div>
      </div>
    </div>
  );
}
