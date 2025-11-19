from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

SVG_TEMPLATE = """<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>
<style>
    text {{ font-family: "Liberation Sans", Arial, sans-serif; fill: #222; }}
    .axis {{ stroke: #333; stroke-width: 2; }}
    .grid {{ stroke: #cccccc; stroke-width: 1; stroke-dasharray: 4 4; }}
</style>
{content}
</svg>"""


COLORS = {
    "normal": "#1f77b4",
    "low": "#d62728",
}


def load_stage5_summary(path: Path) -> List[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    summary = data.get("simuniverse_summary", [])
    if not isinstance(summary, list):
        raise ValueError("stage5 JSON must contain a simuniverse_summary list")
    return summary


def trust_tier(mu_score: float, faizal_score: float) -> str:
    if mu_score < 0.4 and faizal_score > 0.7:
        return "low"
    return "normal"


def project_x(value: float, width: float, padding: float) -> float:
    return padding + value * (width - 2 * padding)


def project_y(value: float, height: float, padding: float) -> float:
    return height - padding - value * (height - 2 * padding)


def create_svg(summary: List[dict], width: int = 720, height: int = 480) -> str:
    padding = 60
    elements: List[str] = []

    # grid lines
    for frac in [0.25, 0.5, 0.75]:
        y = project_y(frac, height, padding)
        elements.append(f"<line class='grid' x1='{padding}' y1='{y}' x2='{width-padding}' y2='{y}' />")
        x = project_x(frac, width, padding)
        elements.append(f"<line class='grid' x1='{x}' y1='{padding}' x2='{x}' y2='{height-padding}' />")

    # axes
    elements.append(f"<line class='axis' x1='{padding}' y1='{height-padding}' x2='{width-padding}' y2='{height-padding}' />")
    elements.append(f"<line class='axis' x1='{padding}' y1='{padding}' x2='{padding}' y2='{height-padding}' />")

    # labels
    elements.append(f"<text x='{width/2}' y='{height-15}' text-anchor='middle' font-size='16'>MUH affinity (higher is better)</text>")
    elements.append(f"<text transform='rotate(-90 {15} {height/2})' x='{15}' y='{height/2}' text-anchor='middle' font-size='16'>Faizal obstruction (lower is better)</text>")
    elements.append(f"<text x='{width/2}' y='{35}' text-anchor='middle' font-size='20'>SimUniverse core evidence map</text>")

    # ticks
    for frac in [0.0, 0.25, 0.5, 0.75, 1.0]:
        x = project_x(frac, width, padding)
        y = project_y(frac, height, padding)
        elements.append(f"<text x='{x}' y='{height-padding+25}' text-anchor='middle' font-size='12'>{frac:.2f}</text>")
        elements.append(f"<text x='{padding-15}' y='{y + 4}' text-anchor='end' font-size='12'>{frac:.2f}</text>")

    # points
    for entry in summary:
        mu = float(entry.get("mu_score", 0.0))
        faizal = float(entry.get("faizal_score", 0.0))
        toe_id = entry.get("toe_candidate_id", "unknown")
        tier = trust_tier(mu, faizal)
        cx = project_x(mu, width, padding)
        cy = project_y(faizal, height, padding)
        color = COLORS[tier]
        elements.append(
            f"<circle cx='{cx}' cy='{cy}' r='10' fill='{color}' stroke='white' stroke-width='2'></circle>"
        )
        elements.append(
            f"<text x='{cx + 12}' y='{cy - 12}' font-size='12' text-anchor='start'>{toe_id}</text>"
        )

    # legend
    legend_y = padding
    for label, color in [("Trusted/normal", COLORS["normal"]), ("Low-trust heuristic", COLORS["low"])]:
        elements.append(
            f"<circle cx='{width - padding - 120}' cy='{legend_y}' r='8' fill='{color}' stroke='white' stroke-width='2'></circle>"
        )
        elements.append(
            f"<text x='{width - padding - 100}' y='{legend_y + 4}' font-size='12' text-anchor='start'>{label}</text>"
        )
        legend_y += 24

    return SVG_TEMPLATE.format(width=width, height=height, content="\n".join(elements))


def write_svg(summary: List[dict], out_path: Path) -> None:
    svg = create_svg(summary)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the SimUniverse core MUH/Faizal graph.")
    parser.add_argument("--stage5-json", required=True, help="Path to Stage-5 summary JSON file.")
    parser.add_argument("--out", required=True, help="Path for the generated SVG graph.")
    args = parser.parse_args()

    summary = load_stage5_summary(Path(args.stage5_json))
    write_svg(summary, Path(args.out))


if __name__ == "__main__":
    main()
