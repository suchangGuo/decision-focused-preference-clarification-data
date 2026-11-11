from __future__ import annotations

import csv
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgb
from matplotlib.transforms import ScaledTranslation


PACKAGE_ROOT = Path(__file__).resolve().parent.parent
SOURCE = (
    PACKAGE_ROOT
    / "mechanism_validation"
    / "interaction_cost"
    / "interaction_cost_summary.csv"
)
OUTPUT = PACKAGE_ROOT / "source_data" / "figures"
OUTPUT.mkdir(parents=True, exist_ok=True)

MM_TO_INCH = 1.0 / 25.4
FIGURE_WIDTH_MM = 89.0
DOUBLE_FIGURE_WIDTH_MM = 178.0

COLORS = {
    "action_stable": "#476A93",
    "cost_aware": "#4C8174",
    "resource": "#D2A24C",
    "structural": "#C8CDD5",
    "queries": "#496F9B",
    "width": "#4F8B7C",
    "mmr": "#626E9B",
    "regret": "#B86A55",
    "axis": "#27313B",
    "grid": "#D9DDE2",
    "panel_fill": "#F2F5F8",
}

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 7.2,
        "axes.labelsize": 7.4,
        "xtick.labelsize": 6.8,
        "ytick.labelsize": 6.8,
        "legend.fontsize": 6.5,
        "axes.linewidth": 0.75,
        "axes.edgecolor": COLORS["axis"],
        "axes.labelcolor": COLORS["axis"],
        "xtick.color": COLORS["axis"],
        "ytick.color": COLORS["axis"],
        "xtick.major.width": 0.65,
        "ytick.major.width": 0.65,
        "xtick.major.size": 2.7,
        "ytick.major.size": 2.7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
    }
)


def read_summary() -> dict[str, np.ndarray]:
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if len(rows) != 4:
        raise ValueError(f"Expected four interaction-cost levels, found {len(rows)}")

    def values(column: str) -> np.ndarray:
        return np.asarray([float(row[column]) for row in rows], dtype=float)

    data = {
        "cost": values("interaction_cost"),
        "action_stable": values("action_stable_share_percent"),
        "cost_aware": values("cost_aware_share_percent"),
        "resource": values("resource_constrained_share_percent"),
        "structural": values("structural_termination_share_percent"),
        "queries": values("mean_query_count"),
        "width": values("mean_remaining_width"),
        "mmr": values("mean_MMR"),
        "regret": values("mean_realized_regret"),
    }

    composition = (
        data["action_stable"]
        + data["cost_aware"]
        + data["resource"]
        + data["structural"]
    )
    if not np.allclose(composition, 100.0, atol=1e-6):
        raise ValueError("Terminal-state shares do not sum to 100%")
    if not np.all(np.diff(data["cost"]) > 0):
        raise ValueError("Interaction-cost levels must be strictly increasing")
    return data


def format_cost_axis(ax: mpl.axes.Axes, *, show_label: bool = True) -> None:
    ticks = np.asarray([0.0, 0.0047, 0.0094, 0.0188])
    ax.set_xlim(-0.0018, 0.0206)
    ax.set_xticks(ticks)
    ax.set_xticklabels(["0", "0.0047", "0.0094", "0.0188"])
    if show_label:
        ax.set_xlabel(r"Interaction cost, $C^{\mathrm{int}}$")


def clean_axis(ax: mpl.axes.Axes, *, shaded: bool = False) -> None:
    ax.set_axisbelow(True)
    ax.set_facecolor(COLORS["panel_fill"] if shaded else "white")
    ax.grid(
        axis="y",
        color="white" if shaded else COLORS["grid"],
        linewidth=0.72 if shaded else 0.45,
        alpha=0.95 if shaded else 0.72,
    )


def mix_color(color: str, target: str, amount: float) -> tuple[float, float, float]:
    base = np.asarray(to_rgb(color))
    destination = np.asarray(to_rgb(target))
    return tuple(base * (1.0 - amount) + destination * amount)


def spherical_line(
    ax: mpl.axes.Axes,
    fig: mpl.figure.Figure,
    x: np.ndarray,
    y: np.ndarray,
    color: str,
) -> None:
    """Draw a restrained Origin-like glossy sphere marker series."""
    ax.plot(x, y, color=color, linewidth=1.45, zorder=3)

    shadow_transform = ax.transData + ScaledTranslation(
        0.75 / 72.0,
        -0.75 / 72.0,
        fig.dpi_scale_trans,
    )
    ax.scatter(
        x,
        y,
        s=52,
        color="#1A2430",
        alpha=0.18,
        linewidth=0,
        transform=shadow_transform,
        zorder=3.2,
        clip_on=True,
    )
    ax.scatter(
        x,
        y,
        s=50,
        color=mix_color(color, "#000000", 0.22),
        edgecolor="white",
        linewidth=0.60,
        zorder=4,
    )
    ax.scatter(
        x,
        y,
        s=37,
        color=mix_color(color, "#FFFFFF", 0.12),
        linewidth=0,
        zorder=4.2,
    )

    highlight_transform = ax.transData + ScaledTranslation(
        -0.75 / 72.0,
        0.75 / 72.0,
        fig.dpi_scale_trans,
    )
    ax.scatter(
        x,
        y,
        s=8,
        color="white",
        alpha=0.72,
        linewidth=0,
        transform=highlight_transform,
        zorder=4.5,
        clip_on=True,
    )


def save_figure(fig: mpl.figure.Figure, stem: str) -> None:
    outputs = {
        "svg": {},
        "pdf": {},
        "png": {"dpi": 450},
        "tiff": {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}},
    }
    for suffix, kwargs in outputs.items():
        fig.savefig(OUTPUT / f"{stem}.{suffix}", **kwargs)
    svg_text = (OUTPUT / f"{stem}.svg").read_text(encoding="utf-8")
    if "<text" not in svg_text:
        raise RuntimeError(f"Editable SVG text check failed for {stem}")
    plt.close(fig)


def plot_stopping_composition(data: dict[str, np.ndarray]) -> None:
    fig = plt.figure(
        figsize=(FIGURE_WIDTH_MM * MM_TO_INCH, 64.0 * MM_TO_INCH)
    )
    ax = fig.add_axes([0.17, 0.20, 0.79, 0.60])
    x = data["cost"]
    bottom = np.zeros_like(x)
    series = [
        ("action_stable", "Action-stable"),
        ("cost_aware", "Cost-aware"),
        ("resource", "Resource-constrained"),
        ("structural", "Structural termination"),
    ]
    for key, label in series:
        ax.bar(
            x,
            data[key],
            width=0.00265,
            bottom=bottom,
            color=COLORS[key],
            edgecolor="white",
            linewidth=0.55,
            label=label,
        )
        bottom += data[key]

    ax.set_ylim(0.0, 100.0)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("Terminal probability mass (%)")
    format_cost_axis(ax)
    clean_axis(ax)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        ncol=2,
        loc="upper center",
        bbox_to_anchor=(0.56, 0.965),
        columnspacing=1.15,
        handlelength=1.35,
        handletextpad=0.45,
        labelspacing=0.45,
    )
    save_figure(fig, "fig_cint_stopping_composition")


def plot_clarification_depth(data: dict[str, np.ndarray]) -> None:
    fig, axes = plt.subplots(
        1,
        2,
        sharex=True,
        figsize=(DOUBLE_FIGURE_WIDTH_MM * MM_TO_INCH, 64.0 * MM_TO_INCH),
    )
    fig.subplots_adjust(
        left=0.085,
        right=0.985,
        bottom=0.27,
        top=0.94,
        wspace=0.30,
    )
    x = data["cost"]

    spherical_line(
        axes[0], fig, x, data["queries"], COLORS["queries"]
    )
    axes[0].set_ylabel("Mean queries")
    axes[0].set_ylim(1.0, 3.18)
    axes[0].set_yticks([1.0, 2.0, 3.0])

    spherical_line(
        axes[1], fig, x, data["width"], COLORS["width"]
    )
    axes[1].set_ylabel("Remaining width")
    axes[1].set_ylim(0.115, 0.202)
    axes[1].set_yticks([0.12, 0.16, 0.20])

    for ax in axes:
        clean_axis(ax, shaded=True)
        format_cost_axis(ax, show_label=False)
    axes[0].text(
        0.00,
        1.03,
        "(a)",
        transform=axes[0].transAxes,
        fontweight="bold",
        va="bottom",
    )
    axes[1].text(
        0.00,
        1.03,
        "(b)",
        transform=axes[1].transAxes,
        fontweight="bold",
        va="bottom",
    )
    fig.supxlabel(r"Interaction cost, $C^{\mathrm{int}}$", y=0.055)
    save_figure(fig, "fig_cint_clarification_depth")


def plot_decision_risk(data: dict[str, np.ndarray]) -> None:
    fig, axes = plt.subplots(
        1,
        2,
        sharex=True,
        figsize=(DOUBLE_FIGURE_WIDTH_MM * MM_TO_INCH, 64.0 * MM_TO_INCH),
    )
    fig.subplots_adjust(
        left=0.090,
        right=0.985,
        bottom=0.27,
        top=0.94,
        wspace=0.32,
    )
    x = data["cost"]

    spherical_line(
        axes[0], fig, x, data["mmr"], COLORS["mmr"]
    )
    axes[0].set_ylabel("Mean MMR")
    axes[0].set_ylim(0.0, 0.029)
    axes[0].set_yticks([0.00, 0.01, 0.02])
    axes[0].yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter("%.2f"))

    spherical_line(
        axes[1], fig, x, data["regret"], COLORS["regret"]
    )
    axes[1].set_ylabel("Realized regret")
    axes[1].set_ylim(0.0, 0.0049)
    axes[1].set_yticks([0.000, 0.002, 0.004])
    axes[1].yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter("%.3f"))

    for ax in axes:
        clean_axis(ax, shaded=True)
        format_cost_axis(ax, show_label=False)
    axes[0].text(
        0.00,
        1.03,
        "(a)",
        transform=axes[0].transAxes,
        fontweight="bold",
        va="bottom",
    )
    axes[1].text(
        0.00,
        1.03,
        "(b)",
        transform=axes[1].transAxes,
        fontweight="bold",
        va="bottom",
    )
    fig.supxlabel(r"Interaction cost, $C^{\mathrm{int}}$", y=0.055)
    save_figure(fig, "fig_cint_decision_risk")


def main() -> None:
    data = read_summary()
    plot_stopping_composition(data)
    plot_clarification_depth(data)
    plot_decision_risk(data)
    print(f"Created 12 figure files in {OUTPUT}")


if __name__ == "__main__":
    main()

