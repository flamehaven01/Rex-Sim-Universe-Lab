import React from "react";
import type { OmegaBadgeProps } from "./types";

function getOmegaColor(level: string): string {
  switch (level) {
    case "Ω-3":
      return "from-violet-400 to-cyan-300 text-slate-950";
    case "Ω-2":
      return "from-indigo-400 to-sky-300 text-slate-950";
    case "Ω-1":
      return "from-slate-400 to-slate-300 text-slate-900";
    default:
      return "from-slate-700 to-slate-600 text-slate-200";
  }
}

function getSimUniverseColor(status: string): string {
  switch (status) {
    case "SimUniverse-Aligned":
      return "border-emerald-400/60 text-emerald-200";
    case "SimUniverse-Qualified":
      return "border-cyan-400/60 text-cyan-200";
    case "SimUniverse-Classical":
      return "border-amber-400/60 text-amber-200";
    case "SimUniverse-Uncertified":
    default:
      return "border-slate-600/80 text-slate-300";
  }
}

export const OmegaSimUniverseHeader: React.FC<OmegaBadgeProps> = ({
  tenant,
  service,
  environment,
  omegaLevel,
  omegaScore,
  simUniverseScore,
  simUniverseStatus,
  lowTrustToeCount,
  lastUpdatedIso,
}) => {
  const omegaColor = getOmegaColor(omegaLevel);
  const simColor = getSimUniverseColor(simUniverseStatus);

  const formattedOmega = omegaScore.toFixed(3);
  const formattedSim = simUniverseScore.toFixed(3);

  return (
    <header className="w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-semibold text-slate-50">{service}</h1>
            <span className="inline-flex items-center gap-1 rounded-full border border-slate-700 px-2 py-0.5 text-[10px] font-medium text-slate-300">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              <span>{tenant}</span>
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-slate-900 px-2 py-0.5 text-[10px] text-slate-300">
              <span className="h-1.5 w-1.5 rounded-full bg-sky-400" />
              <span>{environment}</span>
            </span>
          </div>
          {lastUpdatedIso && (
            <p className="text-[10px] text-slate-500">
              Last Ω / SimUniverse certification update: {" "}
              <time dateTime={lastUpdatedIso}>{lastUpdatedIso}</time>
            </p>
          )}
        </div>

        <div className="flex flex-wrap items-center justify-end gap-2 text-[11px]">
          <div className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r px-3 py-1 shadow-sm shadow-slate-900/80">
            <div className="flex h-5 w-5 items-center justify-center rounded-full bg-slate-950/40 text-[10px] font-semibold">
              Ω
            </div>
            <div className={["font-semibold", omegaColor].join(" ")}>{omegaLevel}</div>
            <span className="ml-1 text-[10px] text-slate-900/80">{formattedOmega}</span>
          </div>

          <div
            className={[
              "inline-flex items-center gap-1 rounded-full border px-3 py-1",
              "bg-slate-950/60",
              simColor,
            ].join(" ")}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-current" />
            <span className="font-medium">{simUniverseStatus}</span>
          </div>

          <div className="inline-flex items-center gap-1 rounded-full bg-slate-900/80 px-3 py-1 text-slate-200">
            <span className="text-[10px] uppercase tracking-wide text-slate-400">
              simuniverse_consistency
            </span>
            <span className="font-mono text-xs">{formattedSim}</span>
          </div>

          {lowTrustToeCount > 0 && (
            <div className="inline-flex items-center gap-1 rounded-full bg-rose-900/40 px-3 py-1 text-rose-200">
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-rose-500/80 text-[9px]">
                !
              </span>
              <span className="font-medium">
                {lowTrustToeCount} low-trust TOE
                {lowTrustToeCount > 1 ? "s" : ""}
              </span>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
