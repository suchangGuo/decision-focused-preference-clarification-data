from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd


mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 7.5,
        "axes.labelsize": 8.4,
        "axes.linewidth": 0.8,
        "xtick.labelsize": 7.2,
        "ytick.labelsize": 7.2,
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
        "xtick.major.size": 3.0,
        "ytick.major.size": 3.0,
        "legend.fontsize": 7.2,
        "legend.frameon": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
    }
)


PACKAGE_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = (
    PACKAGE_ROOT
    / "mechanism_validation"
    / "query_objectives"
    / "query_objective_trajectories.csv"
)
OUTPUT_DIR = PACKAGE_ROOT / "source_data" / "figures"
OUTPUT_STEM = OUTPUT_DIR / "Figure_6_5_query_objective_mismatch"
TOLERANCE = 1e-8


def prepare_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    trajectories = pd.read_csv(INPUT_FILE)
    first_round = trajectories.loc[trajectories["round"] == 1].copy()

    index_columns = [
        "instance_id",
        "spatial_type",
        "instance_seed",
        "hidden_position",
        "hidden_lambda",
    ]
    paired = first_round.pivot_table(
        index=index_columns,
        columns="policy",
        values=["expected_width", "expected_realized_regret"],
        aggfunc="first",
    ).reset_index()

    paired["delta_width"] = (
        paired[("expected_width", "Decision-oriented")]
        - paired[("expected_width", "Width-oriented")]
    )
    paired["delta_regret"] = (
        paired[("expected_realized_regret", "Decision-oriented")]
        - paired[("expected_realized_regret", "Width-oriented")]
    )
    paired.columns = [
        column[0] if isinstance(column, tuple) and column[1] == "" else column
        for column in paired.columns
    ]

    divergent = paired.loc[
        (paired["delta_width"].abs() > TOLERANCE)
        | (paired["delta_regret"].abs() > TOLERANCE)
    ].copy()
    divergent["ranking_conflict"] = (
        divergent["delta_width"] * divergent["delta_regret"] < 0.0
    )
    return paired, divergent


def quadrant_counts(data: pd.DataFrame) -> dict[str, int]:
    x = data["delta_width"]
    y = data["delta_regret"]
    return {
        "upper_left": int(((x < -TOLERANCE) & (y > TOLERANCE)).sum()),
        "upper_right": int(((x > TOLERANCE) & (y > TOLERANCE)).sum()),
        "lower_left": int(((x < -TOLERANCE) & (y < -TOLERANCE)).sum()),
        "lower_right": int(((x > TOLERANCE) & (y < -TOLERANCE)).sum()),
    }


def add_quadrant_backgrounds(ax: plt.Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    conflict_color = "#F7EEDB"
    ax.add_patch(
        Rectangle(
            (xlim[0], 0.0),
            -xlim[0],
            ylim[1],
            facecolor=conflict_color,
            edgecolor="none",
            alpha=0.72,
            zorder=0,
        )
    )
    ax.add_patch(
        Rectangle(
            (0.0, ylim[0]),
            xlim[1],
            -ylim[0],
            facecolor=conflict_color,
            edgecolor="none",
            alpha=0.72,
            zorder=0,
        )
    )


def add_quadrant_labels(ax: plt.Axes) -> None:
    label_style = {
        "fontsize": 7.1,
        "color": "#5A5A5A",
        "linespacing": 1.18,
    }
    conflict_style = dict(label_style)
    conflict_style.update({"color": "#7A5A2B", "fontweight": "semibold"})

    ax.text(
        0.035,
        0.955,
        "Decision-oriented narrower\nbut higher regret",
        transform=ax.transAxes,
        ha="left",
        va="top",
        **conflict_style,
    )
    ax.text(
        0.965,
        0.955,
        "Width-oriented dominates",
        transform=ax.transAxes,
        ha="right",
        va="top",
        **label_style,
    )
    ax.text(
        0.035,
        0.045,
        "Decision-oriented dominates",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        **label_style,
    )
    ax.text(
        0.965,
        0.045,
        "Decision-oriented wider\nbut lower regret",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        **conflict_style,
    )


def draw_figure(data: pd.DataFrame) -> plt.Figure:
    # Double-column journal format: 180 mm × 116 mm.
    fig, ax = plt.subplots(figsize=(7.09, 4.57))
    fig.subplots_adjust(left=0.105, right=0.975, bottom=0.125, top=0.875)

    xlim = (-0.145, 0.145)
    ylim = (-0.060, 0.060)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    add_quadrant_backgrounds(ax, xlim, ylim)

    ax.axvline(0.0, color="#6E6E6E", linewidth=0.85, zorder=1)
    ax.axhline(0.0, color="#6E6E6E", linewidth=0.85, zorder=1)

    palette = {
        "R": "#4477AA",
        "C": "#D98F39",
        "RC": "#2A9D8F",
    }
    markers = {"R": "o", "C": "s", "RC": "^"}
    for spatial_type in ["R", "C", "RC"]:
        subset = data.loc[data["spatial_type"] == spatial_type]
        ax.scatter(
            subset["delta_width"],
            subset["delta_regret"],
            s=34,
            marker=markers[spatial_type],
            color=palette[spatial_type],
            edgecolor="white",
            linewidth=0.65,
            alpha=0.88,
            label=spatial_type,
            zorder=3,
        )

    mean_x = float(data["delta_width"].mean())
    mean_y = float(data["delta_regret"].mean())
    ax.scatter(
        [mean_x],
        [mean_y],
        s=58,
        marker="D",
        color="#222222",
        edgecolor="white",
        linewidth=0.75,
        label="Mean",
        zorder=5,
    )
    ax.annotate(
        "Mean",
        xy=(mean_x, mean_y),
        xytext=(mean_x + 0.021, mean_y - 0.012),
        fontsize=7.1,
        color="#222222",
        ha="left",
        va="top",
        arrowprops={
            "arrowstyle": "-",
            "color": "#4A4A4A",
            "linewidth": 0.7,
            "shrinkA": 2,
            "shrinkB": 4,
        },
        zorder=6,
    )

    add_quadrant_labels(ax)

    ax.set_xlabel(r"$\Delta W$", fontsize=9.4)
    ax.set_ylabel(r"$\Delta R$", fontsize=9.4)
    ax.set_xticks(np.arange(-0.10, 0.101, 0.05))
    ax.set_yticks(np.arange(-0.06, 0.061, 0.02))
    ax.tick_params(axis="both", colors="#333333", direction="out")
    ax.spines["left"].set_color("#333333")
    ax.spines["bottom"].set_color("#333333")

    ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.025),
        ncol=4,
        columnspacing=1.55,
        handletextpad=0.45,
        borderaxespad=0.0,
    )
    return fig


def export_figure(fig: plt.Figure, paired: pd.DataFrame, divergent: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source_columns = [
        "instance_id",
        "spatial_type",
        "instance_seed",
        "hidden_position",
        "hidden_lambda",
        "delta_width",
        "delta_regret",
        "ranking_conflict",
    ]
    divergent.loc[:, source_columns].to_csv(
        OUTPUT_DIR / "Figure_6_5_source_data.csv",
        index=False,
        encoding="utf-8-sig",
    )

    fig.savefig(OUTPUT_STEM.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(OUTPUT_STEM.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(
        OUTPUT_STEM.with_suffix(".png"),
        dpi=450,
        bbox_inches="tight",
    )
    fig.savefig(
        OUTPUT_STEM.with_suffix(".tiff"),
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )

    counts = quadrant_counts(divergent)
    conflict_count = counts["upper_left"] + counts["lower_right"]
    omitted = len(paired) - len(divergent)
    print(f"paired_scenarios={len(paired)}")
    print(f"plotted_scenarios={len(divergent)}")
    print(f"omitted_origin_scenarios={omitted}")
    print(f"ranking_conflicts={conflict_count}")
    print(f"ranking_conflict_share={conflict_count / len(divergent):.6f}")
    print(f"mean_delta_width={divergent['delta_width'].mean():.10f}")
    print(f"mean_delta_regret={divergent['delta_regret'].mean():.10f}")


def main() -> None:
    paired, divergent = prepare_data()
    figure = draw_figure(divergent)
    export_figure(figure, paired, divergent)
    plt.close(figure)


if __name__ == "__main__":
    main()
