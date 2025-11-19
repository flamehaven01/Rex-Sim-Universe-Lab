import React, { useMemo, useState } from "react";
import type { EvidenceLink, HeatmapData, ToeScenario } from "./types";

type Selection = { toe: string; world: string; kind: "mu" | "faizal" } | null;

type HeatmapTableProps = {
  kind: "mu" | "faizal";
  toeCandidates: string[];
  worldIds: string[];
  values: number[][];
  scenarios: Record<string, ToeScenario>;
  selected: Selection;
  onSelect: (selection: { toe: string; world: string; kind: "mu" | "faizal" }) => void;
  color: "cyan" | "rose";
};

type DetailProps = {
  scenario: ToeScenario;
  selected: Selection;
};

const keyFor = (toe: string, world: string): string => `${toe}::${world}`;

const roleBadgeClass = (role: EvidenceLink["role"]): string => {
  if (role === "support") return "bg-emerald-900/50 text-emerald-300";
  if (role === "contest") return "bg-rose-900/50 text-rose-300";
  return "bg-sky-900/50 text-sky-300";
};

const HeatmapTable: React.FC<HeatmapTableProps> = ({
  kind,
  toeCandidates,
  worldIds,
  values,
  scenarios,
  selected,
  onSelect,
  color,
}) => {
  const toColor = (value: number): string => {
    const shade = 0.15 + 0.6 * Math.max(0, Math.min(1, value));
    return color === "cyan"
      ? `rgba(6, 182, 212, ${shade.toFixed(3)})`
      : `rgba(244, 63, 94, ${shade.toFixed(3)})`;
  };

  return (
    <div className="overflow-x-auto border border-slate-800 rounded-2xl bg-slate-950/60">
      <table className="min-w-full text-xs">
        <thead className="bg-slate-900/80 sticky top-0 z-10">
          <tr>
            <th className="px-2 py-2 text-left text-slate-400 font-medium">TOE \\ World</th>
            {worldIds.map((world) => (
              <th key={world} className="px-2 py-2 text-center text-slate-400 font-medium">
                <code>{world}</code>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {toeCandidates.map((toe, i) => (
            <tr key={toe} className="border-t border-slate-900/70">
              <th className="px-2 py-2 text-left text-slate-100 font-medium">
                <code>{toe}</code>
              </th>
              {worldIds.map((world, j) => {
                const scenario = scenarios[keyFor(toe, world)];
                if (!scenario) {
                  return (
                    <td key={world} className="px-2 py-1 text-center text-slate-500">
                      &ndash;
                    </td>
                  );
                }
                const value = values[i]?.[j] ?? 0.0;
                const isSelected =
                  !!selected &&
                  selected.toe === toe &&
                  selected.world === world &&
                  selected.kind === kind;
                return (
                  <td
                    key={world}
                    style={{ backgroundColor: toColor(value) }}
                    className={[
                      "px-2 py-1 text-center align-middle cursor-pointer transition transform",
                      "hover:scale-[1.03] border-l border-slate-900/60",
                      isSelected ? "ring-2 ring-orange-400/70 ring-offset-2 ring-offset-slate-900" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    onClick={() => onSelect({ toe, world, kind })}
                  >
                    <div className="font-semibold text-slate-950 text-[11px]">
                      {value.toFixed(3)}
                    </div>
                    <div className="text-[10px] text-slate-900/80">
                      ū={scenario.mean_undecidability_index.toFixed(2)},
                      E={scenario.energy_feasibility.toFixed(2)}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const DetailPanel: React.FC<DetailProps> = ({ scenario, selected }) => (
  <div className="flex flex-col gap-3 mt-2">
    <div className="flex items-start justify-between gap-2">
      <div>
        <h3 className="text-sm font-semibold text-slate-50">{scenario.toe_candidate_id}</h3>
        <p className="text-xs text-slate-400">
          World: <code>{scenario.world_id}</code>
        </p>
        {selected && (
          <p className="text-[10px] text-slate-500 mt-1">Selected metric: {selected.kind}</p>
        )}
      </div>
      <div className="flex flex-col items-end gap-1">
        <div className="flex gap-1">
          <span className="inline-flex items-center gap-1 rounded-full border border-cyan-500/50 px-2 py-0.5 text-[10px] text-cyan-200">
            <span className="w-2 h-2 rounded-full bg-cyan-400" /> MUH {scenario.mu_score.toFixed(3)}
          </span>
          <span className="inline-flex items-center gap-1 rounded-full border border-rose-500/50 px-2 py-0.5 text-[10px] text-rose-200">
            <span className="w-2 h-2 rounded-full bg-rose-400" /> Faizal {scenario.faizal_score.toFixed(3)}
          </span>
        </div>
        <div className="flex gap-1 text-[10px] text-slate-400">
          <span>ū={scenario.mean_undecidability_index.toFixed(3)}</span>
          <span>&middot; E={scenario.energy_feasibility.toFixed(3)}</span>
          <span>&middot; RG={scenario.rg_phase_index.toFixed(2)}</span>
          <span>&middot; halt={scenario.rg_halting_indicator.toFixed(2)}</span>
        </div>
      </div>
    </div>

    <div>
      <h4 className="text-xs font-semibold text-slate-200 mb-1">Key evidence</h4>
      {scenario.evidence.length === 0 ? (
        <p className="text-xs text-slate-500">
          No explicit evidence links for this TOE candidate in the current corpus.
        </p>
      ) : (
        <ul className="space-y-2">
          {scenario.evidence.slice(0, 5).map((e) => {
            const loc = e.section_label || e.location_hint || "";
            return (
              <li key={e.claim_id} className="text-xs text-slate-200">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className={["px-1.5 py-0.5 rounded-full text-[10px] font-medium", roleBadgeClass(e.role)].join(" ")}>
                    {e.role}
                  </span>
                  <span className="text-[10px] text-slate-400">w={e.weight.toFixed(2)}</span>
                </div>
                <div>
                  <span className="font-semibold">{e.paper_title}</span>
                  {loc && <span className="text-slate-400 text-[11px]">, {loc}</span>}
                </div>
                <div className="text-[11px] text-slate-300">{e.claim_summary}</div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  </div>
);

export const SimUniverseHeatmap: React.FC<{ data: HeatmapData }> = ({ data }) => {
  const [selection, setSelection] = useState<Selection>(null);

  const selectedScenario = useMemo(() => {
    if (!selection) {
      return null;
    }
    return data.scenarios[keyFor(selection.toe, selection.world)] ?? null;
  }, [selection, data.scenarios]);

  return (
    <div className="grid grid-cols-1 xl:grid-cols-[1.5fr_1fr] gap-4">
      <div className="bg-slate-900/90 border border-slate-800/70 rounded-3xl p-4 shadow-2xl">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-50">SimUniverse MUH vs Faizal heatmaps</h2>
            <p className="text-xs text-slate-400">
              Click any cell to inspect TOE evidence and RG / spectral-gap metrics.
            </p>
          </div>
        </div>

        <div className="mt-4">
          <div className="flex items-center gap-2 mb-1 text-xs text-cyan-200">
            <span className="inline-flex items-center gap-2 rounded-full border border-cyan-500/40 px-2 py-0.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400" /> MUH score
            </span>
          </div>
          <HeatmapTable
            kind="mu"
            toeCandidates={data.toe_candidates}
            worldIds={data.world_ids}
            values={data.mu_scores}
            scenarios={data.scenarios}
            selected={selection}
            onSelect={(sel) => setSelection(sel as Selection)}
            color="cyan"
          />
        </div>

        <div className="mt-6">
          <div className="flex items-center gap-2 mb-1 text-xs text-rose-200">
            <span className="inline-flex items-center gap-2 rounded-full border border-rose-500/40 px-2 py-0.5">
              <span className="w-2 h-2 rounded-full bg-rose-400" /> Faizal score
            </span>
          </div>
          <HeatmapTable
            kind="faizal"
            toeCandidates={data.toe_candidates}
            worldIds={data.world_ids}
            values={data.faizal_scores}
            scenarios={data.scenarios}
            selected={selection}
            onSelect={(sel) => setSelection(sel as Selection)}
            color="rose"
          />
        </div>
      </div>

      <div className="bg-slate-900/90 border border-slate-800/70 rounded-3xl p-4 shadow-2xl">
        <h2 className="text-lg font-semibold text-slate-50 mb-2">Selection details</h2>
        {!selectedScenario ? (
          <p className="text-xs text-slate-500">
            No cell selected yet. Choose any entry in the heatmap to view TOE evidence and metrics.
          </p>
        ) : (
          <DetailPanel scenario={selectedScenario} selected={selection} />
        )}
      </div>
    </div>
  );
};
