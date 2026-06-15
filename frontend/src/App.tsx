import { useState } from "react";
import { Activity, BookOpen, Database, HomeIcon } from "lucide-react";

import { runBacktest } from "./api/client";
import { AboutMethodology } from "./pages/AboutMethodology";
import { BacktestLab } from "./pages/BacktestLab";
import { Home } from "./pages/Home";
import { SavedTests } from "./pages/SavedTests";
import type { BacktestRequest, BacktestResponse } from "./types/backtest";

type Page = "lab" | "home" | "methodology" | "saved";

const NAV_ITEMS = [
  { id: "lab" as const, label: "Backtest Lab", icon: Activity },
  { id: "home" as const, label: "Home", icon: HomeIcon },
  { id: "methodology" as const, label: "Methodology", icon: BookOpen },
  { id: "saved" as const, label: "Saved Tests", icon: Database },
];

export default function App() {
  const [page, setPage] = useState<Page>("lab");
  const [result, setResult] = useState<BacktestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRunBacktest(request: BacktestRequest) {
    setLoading(true);
    setError(null);
    try {
      const nextResult = await runBacktest(request);
      setResult(nextResult);
      setPage("lab");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to run the backtest.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-frost text-ink">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-pine">Research Platform</p>
            <h1 className="mt-1 text-xl font-semibold text-ink">Canadian ETF Backtesting & Risk Lab</h1>
          </div>
          <nav className="flex flex-wrap gap-2">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  className={`nav-button ${page === item.id ? "active" : ""}`}
                  onClick={() => setPage(item.id)}
                  type="button"
                >
                  <Icon size={17} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {page === "lab" && (
          <BacktestLab result={result} loading={loading} error={error} onRun={handleRunBacktest} />
        )}
        {page === "home" && <Home />}
        {page === "methodology" && <AboutMethodology />}
        {page === "saved" && <SavedTests />}
      </main>
    </div>
  );
}

