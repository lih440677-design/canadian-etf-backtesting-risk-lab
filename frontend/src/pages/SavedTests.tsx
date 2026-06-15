import { Archive } from "lucide-react";

export function SavedTests() {
  return (
    <section className="panel min-h-[320px]">
      <div className="flex items-center gap-3">
        <Archive className="text-graphite" size={24} />
        <div>
          <p className="section-kicker">Saved Tests</p>
          <h1 className="mt-1 text-2xl font-semibold text-ink">Persistence arrives in a later phase</h1>
        </div>
      </div>
      <div className="empty-state mt-6">
        Saved configurations, result history, reruns, and CSV exports are reserved for the productization phase.
      </div>
    </section>
  );
}
