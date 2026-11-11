from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = (
    PACKAGE_ROOT
    / "mechanism_validation"
    / "action_regions"
    / "action_region_map.csv"
)
OUTPUT_STEM = PACKAGE_ROOT / "source_data" / "figures" / "action_region_partition_map"

TYPE_ORDER = ("R", "C", "RC")
LAMBDA_MIN = 0.30
LAMBDA_MAX = 0.70


def read_regions() -> dict[tuple[str, int], list[dict[str, float | str]]]:
    regions: dict[tuple[str, int], list[dict[str, float | str]]] = defaultdict(list)
    with DATA_FILE.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["spatial_type"], int(row["instance_seed"]))
            regions[key].append(
                {
                    "action": row["action_class_id"],
                    "lower": float(row["region_lower"]),
                    "upper": float(row["region_upper"]),
                }
            )

    for key, intervals in regions.items():
        intervals.sort(key=lambda item: float(item["lower"]))
        if abs(float(intervals[0]["lower"]) - LAMBDA_MIN) > 1e-8:
            raise ValueError(f"{key} does not start at {LAMBDA_MIN:.2f}.")
        if abs(float(intervals[-1]["upper"]) - LAMBDA_MAX) > 1e-8:
            raise ValueError(f"{key} does not end at {LAMBDA_MAX:.2f}.")
        for left, right in zip(intervals, intervals[1:]):
            if abs(float(left["upper"]) - float(right["lower"])) > 1e-8:
                raise ValueError(f"{key} contains a gap or overlap.")

    for kind in TYPE_ORDER:
        seeds = {seed for kind_, seed in regions if kind_ == kind}
        if len(seeds) != 5:
            raise ValueError(f"Expected five {kind} instances, found {len(seeds)}.")
    if len(regions) != 15:
        raise ValueError("Expected 15 formal test instances in total.")
    return regions


def build_row_layout(
    regions: dict[tuple[str, int], list[dict[str, float | str]]]
) -> tuple[list[tuple[str, int, int, float]], list[float]]:
    rows: list[tuple[str, int, int, float]] = []
    separators: list[float] = []
    y = 16.0
    for group_index, kind in enumerate(TYPE_ORDER):
        seeds = sorted(seed for type_name, seed in regions if type_name == kind)
        for replicate, seed in enumerate(seeds, start=1):
            rows.append((kind, seed, replicate, y))
            y -= 1.0
        if group_index < len(TYPE_ORDER) - 1:
            separators.append(y + 0.10)
            y -= 0.80
    return rows, separators


def draw_figure() -> None:
    regions = read_regions()
    rows, separators = build_row_layout(regions)

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "axes.linewidth": 0.8,
            "xtick.major.width": 0.8,
            "xtick.minor.width": 0.6,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )

    fig, ax = plt.subplots(figsize=(7.15, 5.55), facecolor="white")
    ax.set_facecolor("white")

    fill_colors = ("#E8EFF3", "#D1DEE5")
    boundary_color = "#334A5A"
    outline_color = "#92A1AA"
    bar_height = 0.58

    y_ticks: list[float] = []
    y_labels: list[str] = []

    for kind, seed, replicate, y in rows:
        intervals = regions[(kind, seed)]
        for index, interval in enumerate(intervals):
            lower = float(interval["lower"])
            upper = float(interval["upper"])
            ax.add_patch(
                Rectangle(
                    (lower, y - bar_height / 2),
                    upper - lower,
                    bar_height,
                    facecolor=fill_colors[index % 2],
                    edgecolor="none",
                    zorder=2,
                )
            )

        ax.add_patch(
            Rectangle(
                (LAMBDA_MIN, y - bar_height / 2),
                LAMBDA_MAX - LAMBDA_MIN,
                bar_height,
                facecolor="none",
                edgecolor=outline_color,
                linewidth=0.55,
                zorder=3,
            )
        )

        for interval in intervals[:-1]:
            boundary = float(interval["upper"])
            ax.vlines(
                boundary,
                y - bar_height / 2,
                y + bar_height / 2,
                color=boundary_color,
                linewidth=0.9,
                zorder=4,
            )

        y_ticks.append(y)
        y_labels.append(f"{kind}–{replicate}")

    for separator in separators:
        ax.hlines(
            separator,
            LAMBDA_MIN,
            LAMBDA_MAX,
            color="#D8DEE2",
            linewidth=0.7,
            zorder=1,
        )

    ax.set_xlim(LAMBDA_MIN, LAMBDA_MAX)
    ax.set_ylim(min(y_ticks) - 0.75, max(y_ticks) + 0.75)
    ax.set_yticks(y_ticks, labels=y_labels, fontsize=9.2)
    ax.tick_params(axis="y", length=0, pad=8)

    major_ticks = [0.30, 0.40, 0.50, 0.60, 0.70]
    minor_ticks = [0.35, 0.45, 0.55, 0.65]
    ax.set_xticks(major_ticks)
    ax.set_xticklabels([f"{value:.2f}" for value in major_ticks], fontsize=9.2)
    ax.set_xticks(minor_ticks, minor=True)
    ax.tick_params(axis="x", which="major", length=4.0, pad=5)
    ax.tick_params(axis="x", which="minor", length=2.3)
    ax.set_xlabel(r"Preference weight, $\lambda$", fontsize=10.2, labelpad=7)

    ax.grid(axis="x", which="major", color="#E5E9EC", linewidth=0.65, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#59666E")

    fig.subplots_adjust(left=0.12, right=0.985, top=0.985, bottom=0.115)
    fig.savefig(OUTPUT_STEM.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(OUTPUT_STEM.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(
        OUTPUT_STEM.with_suffix(".png"),
        dpi=600,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)


if __name__ == "__main__":
    draw_figure()
