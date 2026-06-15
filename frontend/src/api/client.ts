import type { AssetPreset, BacktestRequest, BacktestResponse } from "../types/backtest";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    let message = "The request failed. Please check the inputs and try again.";
    try {
      const errorBody = (await response.json()) as { detail?: string };
      if (errorBody.detail) {
        message = errorBody.detail;
      }
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export function fetchAssetPresets(): Promise<AssetPreset[]> {
  return request<AssetPreset[]>("/assets/presets");
}

export function runBacktest(payload: BacktestRequest): Promise<BacktestResponse> {
  return request<BacktestResponse>("/backtests/run", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

