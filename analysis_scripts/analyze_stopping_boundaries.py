from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PACKAGE_ROOT / "mechanism_validation" / "stopping_boundaries"
INPUT_FILE = DATA_DIR / "stopping_leaf_results.csv"
OUTPUT_FILE = DATA_DIR / "stopping_diagnostic_summary.csv"


def weighted_mean(data: pd.DataFrame, column: str) -> float:
    subset = data[[column, "path_probability"]].dropna()
    return float(np.average(subset[column], weights=subset["path_probability"]))


def weighted_share(data: pd.DataFrame, condition: pd.Series) -> float:
    return float(
        data.loc[condition, "path_probability"].sum()
        / data["path_probability"].sum()
    )


def main() -> None:
    data = pd.read_csv(INPUT_FILE)
    cost_aware = data.loc[
        data["stop_category"] == "CostAwareDecisionSufficient"
    ].copy()
    structural = data.loc[
        data["stop_category"] == "StructuralTermination"
    ].copy()

    metrics = [
        ("total_scenario_mass", data["path_probability"].sum()),
        ("cost_aware_share", cost_aware["path_probability"].sum()
         / data["path_probability"].sum()),
        ("structural_share", structural["path_probability"].sum()
         / data["path_probability"].sum()),
        ("cost_aware_mean_remaining_width",
         weighted_mean(cost_aware, "remaining_width")),
        ("cost_aware_min_remaining_width", cost_aware["remaining_width"].min()),
        ("cost_aware_max_remaining_width", cost_aware["remaining_width"].max()),
        ("cost_aware_mean_action_regions",
         weighted_mean(cost_aware, "remaining_action_regions")),
        ("cost_aware_min_action_regions",
         cost_aware["remaining_action_regions"].min()),
        ("cost_aware_mean_MMR", weighted_mean(cost_aware, "MMR")),
        ("cost_aware_mean_best_net_query_value",
         weighted_mean(cost_aware, "best_net_query_value")),
        ("cost_aware_mean_forced_action_change_probability",
         weighted_mean(cost_aware, "forced_action_change_probability")),
        ("cost_aware_mean_counterfactual_gross_regret_reduction",
         weighted_mean(cost_aware, "counterfactual_gross_regret_reduction")),
        ("cost_aware_mean_counterfactual_net_gain",
         weighted_mean(cost_aware, "counterfactual_net_gain")),
        ("cost_aware_nonpositive_counterfactual_net_share",
         weighted_share(
             cost_aware,
             cost_aware["counterfactual_net_gain"] <= 1e-9)),
        ("cost_aware_positive_width_share",
         weighted_share(cost_aware, cost_aware["remaining_width"] > 1e-9)),
        ("cost_aware_multiple_action_region_share",
         weighted_share(
             cost_aware,
             cost_aware["remaining_action_regions"] > 1)),
        ("structural_mean_remaining_width",
         weighted_mean(structural, "remaining_width")),
        ("structural_mean_MMR", weighted_mean(structural, "MMR")),
    ]
    pd.DataFrame(metrics, columns=["metric", "value"]).to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
        float_format="%.10f",
    )


if __name__ == "__main__":
    main()
