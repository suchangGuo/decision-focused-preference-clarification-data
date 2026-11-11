#!/usr/bin/env python3
"""Reproducible aggregation for offline trajectory-driven neighborhood design.

The analysis deliberately uses two evidence channels:

* ``*_signature_aggregate.csv`` contains untruncated counts and is the only
  source used for generation, feasibility, acceptance, improvement, and
  distance-reduction rates.
* trajectory CSV files contain selected structural landmarks.  They are used
  only for RequiredCorrection, basin-escape, and rejected-frontier diagnosis.

Candidate neighborhood families are selected by replication thresholds,
separate Pareto screens, and complementary structural roles.  No weighted
aggregate score is constructed.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Mapping, Sequence, Tuple


EPS = 1e-9

AGGREGATE_FIELDS = {
    "event_type", "origin", "signature", "generated", "feasible",
    "accepted", "objective_positive", "distance_positive",
    "joint_positive", "objective_improvement_sum",
    "distance_reduction_sum",
}

TRAJECTORY_FIELDS = {
    "sequence", "event_type", "stage", "iteration", "origin",
    "source_structure", "target_structure", "accepted", "feasible",
    "objective", "objective_improvement", "dA", "dE", "dL", "dR",
    "dTotal", "dTotal_reduction", "gA", "gE", "gLplus", "gLminus",
    "gR", "rejected_frontier",
}

# These records describe generated transitions.  Incumbent/global-best records
# are deliberately excluded because they repeat transitions already observed
# at the local or reconstruction level.
ACTUAL_EVENT_TYPES = {
    "CurrentChanged",          # compatibility with early instrumented runs
    "LocalCurrentChanged",
    "RejectedCandidate",
    "ReconstructionBranch",
}

REQUIRED_LANDMARK_EVENTS = {
    "CurrentChanged",
    "LocalCurrentChanged",
    "IncumbentChanged",
    "GlobalBest",
    "GlobalBestChanged",
    "ReconstructionBranch",
    "RejectedCandidate",
    "DominanceArchiveEntry",
    "FinalC2Entry",
    "FinalState",
}

GLOBAL_BEST_EVENTS = {"GlobalBest", "GlobalBestChanged"}

FAMILY_COVERAGE = {
    "route_topology": frozenset({"E"}),
    "cross_route_reassignment": frozenset({"A", "E", "R"}),
    "level_reallocation": frozenset({"L"}),
    "coupled_topology_level": frozenset({"E", "L"}),
    "coupled_route_level": frozenset({"A", "E", "L", "R"}),
    "multi_route_reconstruction": frozenset({"A", "E", "R"}),
}

ROLE_FAMILIES = {
    "assignment_reallocation": (
        "cross_route_reassignment",
        "coupled_route_level",
    ),
    "route_topology": (
        "route_topology",
        "coupled_topology_level",
        "cross_route_reassignment",
        "coupled_route_level",
    ),
    "level_reallocation": (
        "level_reallocation",
        "coupled_topology_level",
        "coupled_route_level",
    ),
    "basin_escape": (
        "multi_route_reconstruction",
        "coupled_route_level",
        "coupled_topology_level",
        "cross_route_reassignment",
        "route_topology",
    ),
}

OPERATOR_TEMPLATES = {
    "route_topology": "intra-route segment relocation or reversal",
    "cross_route_reassignment": "cross-route relocate or swap",
    "level_reallocation": "reallocate reconnaissance levels under a fixed route plan",
    "coupled_topology_level": "route-segment change with paired level rebalance",
    "coupled_route_level": "cross-route transfer with paired level rebalance",
    "multi_route_reconstruction": "partial multi-route destroy-and-rebuild",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate offline VNS trajectories into transformation-grammar evidence."
    )
    parser.add_argument("inputs", nargs="+", help="CSV files or directories")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--min-generated-support", type=int, default=10)
    parser.add_argument("--min-run-support", type=int, default=2)
    parser.add_argument("--min-type-support", type=int, default=2)
    parser.add_argument("--stagnation-window", type=int, default=20)
    parser.add_argument("--min-neighborhoods", type=int, default=3)
    parser.add_argument("--max-neighborhoods", type=int, default=4)
    parser.add_argument(
        "--large-scale-min-required-prevalence", type=float, default=0.5
    )
    parser.add_argument("--large-scale-min-required-types", type=int, default=2)
    parser.add_argument("--large-scale-min-median-routes", type=float, default=3.0)
    return parser.parse_args()


def discover_files(inputs: Sequence[str]) -> List[Path]:
    files: List[Path] = []
    for item in inputs:
        path = Path(item)
        if path.is_dir():
            files.extend(path.rglob("*.csv"))
        elif path.is_file():
            files.append(path)
        else:
            files.extend(Path().glob(item))
    result = sorted({path.resolve() for path in files})
    if not result:
        raise SystemExit("No CSV files were found.")
    return result


def read_header(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        return set(next(reader, []))


def partition_files(files: Sequence[Path]) -> Tuple[List[Path], List[Path], List[Path]]:
    aggregate: List[Path] = []
    trajectory: List[Path] = []
    ignored: List[Path] = []
    for path in files:
        header = read_header(path)
        if AGGREGATE_FIELDS.issubset(header):
            aggregate.append(path)
        elif TRAJECTORY_FIELDS.issubset(header):
            trajectory.append(path)
        else:
            ignored.append(path)
    if not aggregate:
        raise SystemExit(
            "No signature aggregate CSV was found. Rates must not be estimated "
            "from the truncated trajectory file."
        )
    if not trajectory:
        raise SystemExit(
            "No trajectory CSV with source_structure and target_structure was found."
        )
    return aggregate, trajectory, ignored


def as_float(value: object, default: float = math.nan) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: object, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def as_bool(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator > 0 else 0.0


def safe_median(values: Sequence[float]) -> float:
    return statistics.median(values) if values else 0.0


def parse_metadata(path: Path, row: Mapping[str, object]) -> Tuple[str, str, str]:
    instance = str(row.get("instance_id") or row.get("instance") or "")
    run_id = str(row.get("run_id") or row.get("run") or "")
    searchable = str(path)
    if not instance:
        match = re.search(r"(\d+-\d+-(?:RC|R|C))", searchable, re.IGNORECASE)
        instance = match.group(1).upper() if match else path.stem
    if not run_id:
        match = re.search(r"run[_-]?(\d+)", searchable, re.IGNORECASE)
        run_id = match.group(1) if match else "1"
    spatial_type = str(row.get("spatial_type") or row.get("type") or "")
    if not spatial_type:
        upper = instance.upper()
        spatial_type = "RC" if upper.endswith("-RC") else (
            "C" if upper.endswith("-C") else ("R" if upper.endswith("-R") else "Unknown")
        )
    return instance, run_id, spatial_type.upper()


def parse_bucket_value(value: str) -> int:
    text = value.strip()
    return int(text[:-1]) if text.endswith("+") else as_int(text)


def parse_signature(signature: str) -> Tuple[int, int, int, int, int]:
    parts = signature.split("|")
    if len(parts) != 5:
        raise ValueError(f"Invalid transformation signature bucket: {signature!r}")
    return tuple(parse_bucket_value(part) for part in parts)  # type: ignore[return-value]


def transition_family(a: int, e: int, level_plus: int, level_minus: int, routes: int) -> str:
    level = level_plus + level_minus
    if a == 0:
        if e == 0:
            return "level_reallocation" if level > 0 else "no_structural_change"
        return "coupled_topology_level" if level > 0 else "route_topology"
    if a >= 3 and routes >= 3:
        return "multi_route_reconstruction"
    return "coupled_route_level" if level > 0 else "cross_route_reassignment"


def correction_family(a: int, e: int, level: int, routes: int) -> str:
    if a == 0:
        if e == 0:
            return "level_reallocation" if level > 0 else "exact_or_equivalent"
        return "coupled_topology_level" if level > 0 else "route_topology"
    if a >= 3 and routes >= 3:
        return "multi_route_reconstruction"
    return "coupled_route_level" if level > 0 else "cross_route_reassignment"


def load_aggregate_rows(files: Sequence[Path]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for path in files:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for raw in csv.DictReader(handle):
                event_type = str(raw["event_type"])
                if event_type not in ACTUAL_EVENT_TYPES:
                    continue
                a, e, lp, lm, routes = parse_signature(str(raw["signature"]))
                family = transition_family(a, e, lp, lm, routes)
                if family == "no_structural_change":
                    continue
                instance, run_id, spatial_type = parse_metadata(path, raw)
                rows.append({
                    "source_file": str(path),
                    "instance": instance,
                    "run_id": run_id,
                    "run_key": f"{instance}|{run_id}",
                    "spatial_type": spatial_type,
                    "event_type": event_type,
                    "origin": str(raw["origin"]),
                    "signature": str(raw["signature"]),
                    "family": family,
                    "gA": a,
                    "gE": e,
                    "gLplus": lp,
                    "gLminus": lm,
                    "gR": routes,
                    **{field: as_int(raw[field]) for field in (
                        "generated", "feasible", "accepted", "objective_positive",
                        "distance_positive", "joint_positive",
                    )},
                    "objective_improvement_sum": as_float(raw["objective_improvement_sum"], 0.0),
                    "distance_reduction_sum": as_float(raw["distance_reduction_sum"], 0.0),
                })
    return rows


def load_trajectory_rows(files: Sequence[Path]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for path in files:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for raw in csv.DictReader(handle):
                instance, run_id, spatial_type = parse_metadata(path, raw)
                item: Dict[str, object] = dict(raw)
                item.update({
                    "source_file": str(path),
                    "instance": instance,
                    "run_id": run_id,
                    "run_key": f"{instance}|{run_id}",
                    "spatial_type": spatial_type,
                    "sequence": as_int(raw["sequence"]),
                    "iteration": as_int(raw["iteration"]),
                    "accepted": as_bool(raw["accepted"]),
                    "feasible": as_bool(raw["feasible"]),
                    "objective": as_float(raw["objective"]),
                    "objective_improvement": as_float(raw["objective_improvement"], 0.0),
                    "dA": as_int(raw["dA"]),
                    "dE": as_int(raw["dE"]),
                    "dL": as_int(raw["dL"]),
                    "dR": as_int(raw["dR"]),
                    "dTotal": as_float(raw["dTotal"]),
                    "dTotal_reduction": as_float(raw["dTotal_reduction"], 0.0),
                    "gA": as_int(raw["gA"]),
                    "gE": as_int(raw["gE"]),
                    "gLplus": as_int(raw["gLplus"]),
                    "gLminus": as_int(raw["gLminus"]),
                    "gR": as_int(raw["gR"]),
                    "rejected_frontier": as_bool(raw["rejected_frontier"]),
                })
                rows.append(item)
    return rows


def canonical_structure_key(encoded: object) -> str:
    """Canonicalize homogeneous UAV labels and reversed closed routes."""
    text = str(encoded or "").strip()
    if not text:
        return ""
    routes: List[str] = []
    for token in text.split("||"):
        match = re.fullmatch(r"u\d+\[(.*)\]", token.strip())
        body = match.group(1) if match else token.strip()
        tuples = [] if body == "" else body.split(">")
        forward = ">".join(tuples)
        reverse = ">".join(reversed(tuples))
        routes.append(min(forward, reverse))
    return "||".join(sorted(routes))


def count_summary(group: Sequence[Mapping[str, object]]) -> Dict[str, object]:
    sums = {
        field: sum(int(row[field]) for row in group)
        for field in (
            "generated", "feasible", "accepted", "objective_positive",
            "distance_positive", "joint_positive",
        )
    }
    generated = sums["generated"]
    feasible = sums["feasible"]
    return {
        **sums,
        "run_support": len({str(row["run_key"]) for row in group}),
        "instance_support": len({str(row["instance"]) for row in group}),
        "type_support": len({str(row["spatial_type"]) for row in group}),
        "feasibility_rate": ratio(sums["feasible"], generated),
        "accepted_rate": ratio(sums["accepted"], generated),
        "accepted_given_feasible": ratio(sums["accepted"], feasible),
        "improvement_rate": ratio(sums["objective_positive"], generated),
        "improvement_given_feasible": ratio(sums["objective_positive"], feasible),
        "distance_reduction_rate": ratio(sums["distance_positive"], generated),
        "joint_positive_rate": ratio(sums["joint_positive"], generated),
        "net_objective_improvement_per_generated": ratio(
            sum(float(row["objective_improvement_sum"]) for row in group), generated
        ),
        "net_distance_reduction_per_generated": ratio(
            sum(float(row["distance_reduction_sum"]) for row in group), generated
        ),
    }


def summarize_actual(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    groups: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[str(row["family"])].append(row)
    return [
        {"family": family, **count_summary(group)}
        for family, group in sorted(groups.items())
    ]


def summarize_origin(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    groups: Dict[Tuple[str, str, str], List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["family"]), str(row["event_type"]), str(row["origin"]))].append(row)
    return [
        {"family": key[0], "event_type": key[1], "origin": key[2], **count_summary(group)}
        for key, group in sorted(groups.items())
    ]


def choose_required_records(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    by_run: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_run[str(row["run_key"])].append(row)

    retained: List[Dict[str, object]] = []
    for run_rows in by_run.values():
        explicit = [row for row in run_rows if str(row["event_type"]) == "RequiredCorrection"]
        candidates = explicit or [
            row for row in run_rows
            if str(row["event_type"]) in REQUIRED_LANDMARK_EVENTS
        ]
        unique: Dict[Tuple[object, ...], Dict[str, object]] = {}
        for row in candidates:
            is_explicit = str(row["event_type"]) == "RequiredCorrection"
            # RequiredCorrection is encoded as selected state -> exact target.
            # Its target distances are therefore zero; the required correction
            # is the event transformation signature and the state to deduplicate
            # is source_structure.  For legacy landmark rows, d* already denotes
            # the target state's distance to the exact solution.
            structure = canonical_structure_key(
                row.get("source_structure") if is_explicit else row.get("target_structure")
            )
            required_a = int(row["gA"]) if is_explicit else int(row["dA"])
            required_e = int(row["gE"]) if is_explicit else int(row["dE"])
            required_l = (
                int(row["gLplus"]) + int(row["gLminus"])
                if is_explicit else int(row["dL"])
            )
            required_r = int(row["gR"]) if is_explicit else int(row["dR"])
            required_total = (
                float(row["dTotal_reduction"])
                if is_explicit else float(row["dTotal"])
            )
            key: Tuple[object, ...]
            if structure:
                key = (row["run_key"], structure)
            else:
                key = (
                    row["run_key"], required_a, required_e, required_l, required_r,
                    round(float(row["objective"]), 10),
                )
            if key not in unique:
                item = dict(row)
                item["canonical_correction_source"] = structure
                item["canonical_exact_target"] = canonical_structure_key(
                    row.get("target_structure") if is_explicit else ""
                )
                item["required_dA"] = required_a
                item["required_dE"] = required_e
                item["required_dL"] = required_l
                item["required_dR"] = required_r
                item["required_dTotal"] = required_total
                item["family"] = correction_family(
                    required_a, required_e, required_l, required_r
                )
                unique[key] = item
        retained.extend(unique.values())
    return retained


def summarize_corrections(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    groups: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        if row["family"] != "exact_or_equivalent":
            groups[str(row["family"])].append(row)
    all_runs = len({str(row["run_key"]) for row in rows})
    output: List[Dict[str, object]] = []
    for family, group in sorted(groups.items()):
        run_support = len({str(row["run_key"]) for row in group})
        output.append({
            "family": family,
            "required_support": len(group),
            "required_run_support": run_support,
            "required_instance_support": len({str(row["instance"]) for row in group}),
            "required_type_support": len({str(row["spatial_type"]) for row in group}),
            "required_run_prevalence": ratio(run_support, all_runs),
            "median_required_dA": safe_median([int(row["required_dA"]) for row in group]),
            "median_required_dE": safe_median([int(row["required_dE"]) for row in group]),
            "median_required_dL": safe_median([int(row["required_dL"]) for row in group]),
            "median_required_dR": safe_median([int(row["required_dR"]) for row in group]),
            "median_required_dTotal": safe_median([
                float(row["required_dTotal"]) for row in group
            ]),
        })
    return output


def build_basin_escapes(
    rows: Sequence[Dict[str, object]], stagnation_window: int
) -> List[Dict[str, object]]:
    groups: Dict[Tuple[str, str], List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["run_key"]), str(row["stage"]))].append(row)

    escapes: Dict[Tuple[object, ...], Dict[str, object]] = {}
    for group in groups.values():
        last_best_iteration = 0
        for row in sorted(group, key=lambda item: (int(item["iteration"]), int(item["sequence"]))):
            event_type = str(row["event_type"])
            is_best = event_type in GLOBAL_BEST_EVENTS
            is_accepted_reconstruction = (
                event_type == "ReconstructionBranch"
                and bool(row["accepted"])
                and "ReconstructionAccepted" in str(row["origin"])
            )
            stagnation = int(row["iteration"]) - last_best_iteration
            qualifies = (
                (is_best or is_accepted_reconstruction)
                and float(row["objective_improvement"]) > EPS
                and stagnation >= stagnation_window
            )
            if qualifies:
                family = transition_family(
                    int(row["gA"]), int(row["gE"]), int(row["gLplus"]),
                    int(row["gLminus"]), int(row["gR"]),
                )
                if family != "no_structural_change":
                    key = (
                        row["run_key"], row["stage"], row["iteration"],
                        canonical_structure_key(row.get("target_structure")),
                    )
                    item = dict(row)
                    item["family"] = family
                    item["stagnation_length"] = stagnation
                    existing = escapes.get(key)
                    if existing is None or is_best:
                        escapes[key] = item
            if is_best:
                last_best_iteration = int(row["iteration"])
    return list(escapes.values())


def summarize_basin_escapes(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    groups: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[str(row["family"])].append(row)
    output: List[Dict[str, object]] = []
    for family, group in sorted(groups.items()):
        output.append({
            "family": family,
            "basin_escapes": len(group),
            "basin_escape_run_support": len({str(row["run_key"]) for row in group}),
            "basin_escape_type_support": len({str(row["spatial_type"]) for row in group}),
            "median_stagnation_length": safe_median([
                int(row["stagnation_length"]) for row in group
            ]),
            "median_escape_objective_improvement": safe_median([
                float(row["objective_improvement"]) for row in group
            ]),
            "median_escape_distance_reduction": safe_median([
                float(row["dTotal_reduction"]) for row in group
            ]),
        })
    return output


def summarize_rejected_frontier(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    groups: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        if str(row["event_type"]) != "RejectedCandidate" or not bool(row["rejected_frontier"]):
            continue
        family = transition_family(
            int(row["gA"]), int(row["gE"]), int(row["gLplus"]),
            int(row["gLminus"]), int(row["gR"]),
        )
        if family != "no_structural_change":
            groups[family].append(row)
    output: List[Dict[str, object]] = []
    for family, group in sorted(groups.items()):
        barriers = [
            row for row in group
            if float(row["dTotal_reduction"]) > EPS
            and float(row["objective_improvement"]) <= EPS
        ]
        output.append({
            "family": family,
            "retained_support": len(group),
            "run_support": len({str(row["run_key"]) for row in group}),
            "type_support": len({str(row["spatial_type"]) for row in group}),
            "distance_reducing_support": sum(
                float(row["dTotal_reduction"]) > EPS for row in group
            ),
            "acceptance_barrier_support": len(barriers),
            "median_barrier_distance_reduction": safe_median([
                float(row["dTotal_reduction"]) for row in barriers
            ]),
        })
    return output


def pareto_front(rows: Sequence[Dict[str, object]], metrics: Sequence[str]) -> set[str]:
    front: set[str] = set()
    for candidate in rows:
        dominated = False
        for other in rows:
            if other is candidate:
                continue
            no_worse = all(float(other[m]) >= float(candidate[m]) - EPS for m in metrics)
            better = any(float(other[m]) > float(candidate[m]) + EPS for m in metrics)
            if no_worse and better:
                dominated = True
                break
        if not dominated:
            front.add(str(candidate["family"]))
    return front


def merge_evidence(
    actual: Sequence[Dict[str, object]],
    corrections: Sequence[Dict[str, object]],
    basin: Sequence[Dict[str, object]],
    min_generated: int,
    min_runs: int,
    min_types: int,
) -> List[Dict[str, object]]:
    actual_map = {str(row["family"]): row for row in actual}
    correction_map = {str(row["family"]): row for row in corrections}
    basin_map = {str(row["family"]): row for row in basin}
    families = sorted(set(actual_map) | set(correction_map) | set(basin_map))
    merged: List[Dict[str, object]] = []
    defaults = {
        "generated": 0, "feasible": 0, "accepted": 0,
        "objective_positive": 0, "distance_positive": 0, "joint_positive": 0,
        "run_support": 0, "instance_support": 0, "type_support": 0,
        "feasibility_rate": 0.0, "accepted_rate": 0.0,
        "accepted_given_feasible": 0.0, "improvement_rate": 0.0,
        "improvement_given_feasible": 0.0, "distance_reduction_rate": 0.0,
        "joint_positive_rate": 0.0, "net_objective_improvement_per_generated": 0.0,
        "net_distance_reduction_per_generated": 0.0,
        "required_support": 0, "required_run_support": 0,
        "required_instance_support": 0, "required_type_support": 0,
        "required_run_prevalence": 0.0, "median_required_dA": 0.0,
        "median_required_dE": 0.0, "median_required_dL": 0.0,
        "median_required_dR": 0.0, "median_required_dTotal": 0.0,
        "basin_escapes": 0,
        "basin_escape_run_support": 0, "basin_escape_type_support": 0,
        "median_stagnation_length": 0.0,
        "median_escape_objective_improvement": 0.0,
        "median_escape_distance_reduction": 0.0,
    }
    for family in families:
        row: Dict[str, object] = {"family": family, **defaults}
        row.update(actual_map.get(family, {}))
        row.update(correction_map.get(family, {}))
        row.update(basin_map.get(family, {}))
        row["basin_escape_run_rate"] = ratio(
            int(row["basin_escape_run_support"]), int(row["run_support"])
        )
        actual_replicated = (
            int(row["generated"]) >= min_generated
            and int(row["run_support"]) >= min_runs
            and int(row["type_support"]) >= min_types
        )
        required_replicated = (
            int(row["required_run_support"]) >= min_runs
            and int(row["required_type_support"]) >= min_types
        )
        basin_replicated = (
            int(row["basin_escape_run_support"]) >= min_runs
            and int(row["basin_escape_type_support"]) >= min_types
        )
        directional = (
            int(row["objective_positive"]) > 0
            or int(row["distance_positive"]) > 0
            or int(row["basin_escape_run_support"]) > 0
        )
        row["actual_replicated"] = actual_replicated
        row["required_replicated"] = required_replicated
        row["basin_replicated"] = basin_replicated
        row["eligible"] = (
            (actual_replicated and directional)
            or required_replicated
            or basin_replicated
        )
        channels = []
        if actual_replicated:
            channels.append("actual")
        if basin_replicated:
            channels.append("basin")
        if required_replicated:
            channels.append("required")
        row["evidence_channel"] = "+".join(channels) or "insufficient"
        row["structural_coverage"] = "+".join(sorted(FAMILY_COVERAGE.get(family, ())))
        row["operator_template"] = OPERATOR_TEMPLATES.get(family, "")
        merged.append(row)

    actual_pool = [row for row in merged if bool(row["actual_replicated"])]
    required_pool = [row for row in merged if bool(row["required_replicated"])]
    actual_front = pareto_front(actual_pool, (
        "run_support", "type_support", "feasibility_rate", "improvement_rate",
        "distance_reduction_rate", "joint_positive_rate", "basin_escape_run_support",
    )) if actual_pool else set()
    required_front = pareto_front(required_pool, (
        "required_run_support", "required_type_support", "required_run_prevalence",
    )) if required_pool else set()
    for row in merged:
        row["actual_pareto"] = str(row["family"]) in actual_front
        row["required_pareto"] = str(row["family"]) in required_front
    return merged


def select_complementary_families(
    rows: List[Dict[str, object]],
    minimum: int,
    maximum: int,
    large_scale_min_prevalence: float,
    large_scale_min_types: int,
    large_scale_min_routes: float,
) -> None:
    """Select distinct role representatives by a documented decision chain.

    The tuple below is a lexicographic tie-break, not a weighted score.  The
    separate Pareto flags prevent one outcome metric from compensating for
    uniformly weaker evidence on every other metric.
    """
    pool = [row for row in rows if bool(row["eligible"])]
    selected: List[Dict[str, object]] = []
    reasons: Dict[str, List[str]] = defaultdict(list)

    actual_metrics = (
        "run_support", "type_support", "feasibility_rate", "improvement_rate",
        "distance_reduction_rate", "joint_positive_rate", "basin_escape_run_support",
    )
    required_metrics = (
        "required_run_support", "required_type_support", "required_run_prevalence",
    )

    def mark_role_pareto(candidates: Sequence[Dict[str, object]]) -> None:
        actual_candidates = [row for row in candidates if bool(row["actual_replicated"])]
        required_candidates = [row for row in candidates if bool(row["required_replicated"])]
        actual_front = pareto_front(actual_candidates, actual_metrics) if actual_candidates else set()
        required_front = pareto_front(required_candidates, required_metrics) if required_candidates else set()
        for row in candidates:
            row["_role_actual_pareto"] = str(row["family"]) in actual_front
            row["_role_required_pareto"] = str(row["family"]) in required_front

    def evidence_rank(row: Mapping[str, object], role: str) -> Tuple[object, ...]:
        if role == "basin_escape":
            channel = (
                int(bool(row["basin_replicated"])),
                int(bool(row["actual_replicated"])),
                int(bool(row["required_replicated"])),
            )
        else:
            channel = (
                int(bool(row["actual_replicated"])),
                int(bool(row["required_replicated"])),
                int(bool(row["basin_replicated"])),
            )
        role_families = ROLE_FAMILIES[role]
        role_fit = len(role_families) - role_families.index(str(row["family"]))
        if role == "basin_escape":
            role_outcome = (
                int(row["basin_escape_run_support"]),
                int(row["basin_escapes"]),
                float(row["joint_positive_rate"]),
            )
        else:
            role_outcome = (
                float(row["joint_positive_rate"]),
                float(row["distance_reduction_rate"]),
                float(row["improvement_rate"]),
            )
        return (
            *channel,
            int(bool(row.get("_role_actual_pareto", row["actual_pareto"])))
            + int(bool(row.get("_role_required_pareto", row["required_pareto"]))),
            max(int(row["type_support"]), int(row["required_type_support"])),
            max(int(row["run_support"]), int(row["required_run_support"])),
            *role_outcome,
            float(row["feasibility_rate"]),
            role_fit,
            str(row["family"]),
        )

    # The three refinement roles must be represented by distinct families when
    # the replicated evidence permits it; otherwise a broad coupled family
    # could mask the need for a topology- or level-specific operator.
    for role in ("assignment_reallocation", "route_topology", "level_reallocation"):
        candidates = [
            row for row in pool
            if str(row["family"]) in ROLE_FAMILIES[role] and row not in selected
        ]
        if not candidates:
            continue
        mark_role_pareto(candidates)
        choice = max(candidates, key=lambda row: evidence_rank(row, role))
        if len(selected) < maximum:
            selected.append(choice)
            reasons[str(choice["family"])].append(role)

    # Multi-route reconstruction is not a generic assignment neighborhood.  It
    # occupies a separate fourth slot only when the RequiredCorrection evidence
    # shows a replicated large-scale deficit.
    large_scale = None
    for row in rows:
        qualified = (
            str(row["family"]) == "multi_route_reconstruction"
            and bool(row["required_replicated"])
            and float(row["required_run_prevalence"]) >= large_scale_min_prevalence
            and int(row["required_type_support"]) >= large_scale_min_types
            and float(row["median_required_dR"]) >= large_scale_min_routes
        )
        row["large_scale_escape_qualified"] = qualified
        if qualified:
            large_scale = row

    if large_scale is not None and len(selected) < maximum:
        if large_scale not in selected:
            selected.append(large_scale)
        reasons[str(large_scale["family"])].append("large_scale_escape")

    escape_candidates = [
        row for row in pool
        if str(row["family"]) in ROLE_FAMILIES["basin_escape"]
        and str(row["family"]) != "multi_route_reconstruction"
        and (
            int(row["basin_escape_run_support"]) > 0
            or float(row["median_required_dR"]) >= 3
        )
    ]
    if escape_candidates:
        mark_role_pareto(escape_candidates)
        choice = max(
            escape_candidates,
            key=lambda row: evidence_rank(row, "basin_escape"),
        )
        if choice not in selected and len(selected) < maximum:
            selected.append(choice)
        if choice in selected:
            reasons[str(choice["family"])].append("basin_escape")

    for row in rows:
        row.pop("_role_actual_pareto", None)
        row.pop("_role_required_pareto", None)

    selected = selected[:maximum]
    selected_names = {str(row["family"]) for row in selected}
    shortfall = max(0, min(minimum, maximum) - len(selected))
    for row in rows:
        family = str(row["family"])
        row["selected"] = family in selected_names
        row["selection_shortfall"] = shortfall
        row["selected_role"] = ";".join(reasons.get(family, ()))
        bases: List[str] = []
        if bool(row["actual_pareto"]):
            bases.append("actual_pareto")
        if bool(row["required_pareto"]):
            bases.append("required_pareto")
        if family in selected_names:
            bases.append(str(row["evidence_channel"]))
        row["selection_basis"] = ";".join(bases)


def write_csv(path: Path, rows: Sequence[Mapping[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: Sequence[Mapping[str, object]], fields: Sequence[str]) -> str:
    if not rows:
        return "_No records._"
    lines = ["| " + " | ".join(fields) + " |", "|" + "---|" * len(fields)]
    for row in rows:
        values = []
        for field in fields:
            value = row.get(field, "")
            values.append(f"{value:.4f}" if isinstance(value, float) else str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_report(
    path: Path,
    aggregate_files: Sequence[Path],
    trajectory_files: Sequence[Path],
    ignored_files: Sequence[Path],
    actual: Sequence[Dict[str, object]],
    corrections: Sequence[Dict[str, object]],
    basin: Sequence[Dict[str, object]],
    candidates: Sequence[Dict[str, object]],
    stagnation_window: int,
    min_generated: int,
    min_runs: int,
    min_types: int,
    min_neighborhoods: int,
    max_neighborhoods: int,
    large_scale_min_prevalence: float,
    large_scale_min_types: int,
    large_scale_min_routes: float,
) -> None:
    selected = [row for row in candidates if bool(row.get("selected"))]
    report = f"""# Offline trajectory-driven neighborhood design report

## Data boundary

- Full signature-aggregate files: {len(aggregate_files)}
- Selected-node trajectory files: {len(trajectory_files)}
- Ignored non-input CSV files: {len(ignored_files)}
- Basin-escape stagnation window: {stagnation_window} iterations
- Minimum generated support: {min_generated}
- Minimum independent-run support: {min_runs}
- Minimum spatial-type support: {min_types}
- Requested frozen family count: {min_neighborhoods}--{max_neighborhoods}
- Large-scale escape minimum correction prevalence: {large_scale_min_prevalence:.2f}
- Large-scale escape minimum type support: {large_scale_min_types}
- Large-scale escape minimum median affected routes: {large_scale_min_routes:.2f}

All rates below use untruncated signature aggregates.  Trajectory rows are not
used as denominators because rejected candidates are retained on a bounded
(objective, distance) frontier.  Exact solutions are used only for offline
distance labeling, and the resulting neighborhood set must be frozen before
held-out algorithm evaluation.

## Actual transition grammar

{markdown_table(actual, (
    "family", "generated", "run_support", "type_support", "feasibility_rate",
    "accepted_rate", "improvement_rate", "distance_reduction_rate",
    "joint_positive_rate",
))}

## RequiredCorrection grammar

For explicit RequiredCorrection events the target is the exact solution;
therefore the required components are read from the event's transformation
signature (gA, gE, gLplus + gLminus, gR), not from the target's zero d-fields.

{markdown_table(corrections, (
    "family", "required_support", "required_run_support", "required_type_support",
    "required_run_prevalence", "median_required_dA", "median_required_dE",
    "median_required_dL", "median_required_dR",
))}

## Basin escapes

{markdown_table(basin, (
    "family", "basin_escapes", "basin_escape_run_support",
    "basin_escape_type_support", "median_stagnation_length",
))}

## Frozen candidate neighborhood families

Selection is a rule chain rather than a weighted score: replication thresholds,
separate Pareto screens for demonstrated transitions and RequiredCorrection,
then distinct assignment, topology, and level-refinement roles.  Multi-route
reconstruction is admitted as a fourth, large-scale escape role only when its
RequiredCorrection prevalence, type support, and median affected-route count
meet the declared thresholds.  No redundant family is added merely to reach a
requested count.  A family supported only by RequiredCorrection is a design
requirement, not demonstrated search effectiveness.

{markdown_table(selected, (
    "family", "selected_role", "evidence_channel", "selection_basis",
    "structural_coverage", "operator_template",
))}

## Interpretation boundary

1. Treat aggregate counts as the only source of generation and success rates.
2. Treat RequiredCorrection as structural demand, not an observed successful move.
3. Treat retained rejected candidates as acceptance-barrier diagnostics only.
4. Freeze the selected 3--4 operators before testing unseen seeds or instances.
5. Report held-out performance separately from this operator-design experiment.
"""
    path.write_text(report, encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.min_neighborhoods < 1 or args.max_neighborhoods < args.min_neighborhoods:
        raise SystemExit("Require 1 <= min-neighborhoods <= max-neighborhoods.")
    if not 0.0 <= args.large_scale_min_required_prevalence <= 1.0:
        raise SystemExit("large-scale-min-required-prevalence must be in [0, 1].")
    if args.large_scale_min_required_types < 1:
        raise SystemExit("large-scale-min-required-types must be positive.")
    if args.large_scale_min_median_routes < 1.0:
        raise SystemExit("large-scale-min-median-routes must be at least 1.")
    files = discover_files(args.inputs)
    aggregate_files, trajectory_files, ignored_files = partition_files(files)
    aggregate_rows = load_aggregate_rows(aggregate_files)
    trajectory_rows = load_trajectory_rows(trajectory_files)

    actual = summarize_actual(aggregate_rows)
    origin = summarize_origin(aggregate_rows)
    required_records = choose_required_records(trajectory_rows)
    corrections = summarize_corrections(required_records)
    basin_records = build_basin_escapes(trajectory_rows, args.stagnation_window)
    basin = summarize_basin_escapes(basin_records)
    rejected = summarize_rejected_frontier(trajectory_rows)
    candidates = merge_evidence(
        actual, corrections, basin,
        args.min_generated_support, args.min_run_support, args.min_type_support,
    )
    select_complementary_families(
        candidates, args.min_neighborhoods, args.max_neighborhoods,
        args.large_scale_min_required_prevalence,
        args.large_scale_min_required_types,
        args.large_scale_min_median_routes,
    )

    output = Path(args.output_dir)
    common_actual_fields = [
        "family", "generated", "feasible", "accepted", "objective_positive",
        "distance_positive", "joint_positive", "run_support", "instance_support",
        "type_support", "feasibility_rate", "accepted_rate",
        "accepted_given_feasible", "improvement_rate", "improvement_given_feasible",
        "distance_reduction_rate", "joint_positive_rate",
        "net_objective_improvement_per_generated",
        "net_distance_reduction_per_generated",
    ]
    write_csv(output / "actual_transition_summary.csv", actual, common_actual_fields)
    write_csv(
        output / "origin_transition_summary.csv", origin,
        ["family", "event_type", "origin"] + common_actual_fields[1:],
    )
    write_csv(output / "required_correction_summary.csv", corrections, [
        "family", "required_support", "required_run_support",
        "required_instance_support", "required_type_support",
        "required_run_prevalence", "median_required_dA", "median_required_dE",
        "median_required_dL", "median_required_dR", "median_required_dTotal",
    ])
    write_csv(output / "required_correction_records.csv", required_records, [
        "source_file", "instance", "run_id", "spatial_type", "event_type",
        "stage", "iteration", "origin", "family", "required_dA", "required_dE",
        "required_dL", "required_dR", "required_dTotal", "objective",
        "canonical_correction_source", "canonical_exact_target",
    ])
    write_csv(output / "basin_escape_summary.csv", basin, [
        "family", "basin_escapes", "basin_escape_run_support",
        "basin_escape_type_support", "median_stagnation_length",
        "median_escape_objective_improvement", "median_escape_distance_reduction",
    ])
    write_csv(output / "rejected_frontier_summary.csv", rejected, [
        "family", "retained_support", "run_support", "type_support",
        "distance_reducing_support", "acceptance_barrier_support",
        "median_barrier_distance_reduction",
    ])
    write_csv(output / "candidate_neighborhoods.csv", candidates, [
        "family", "eligible", "actual_replicated", "basin_replicated",
        "required_replicated",
        "actual_pareto", "required_pareto", "large_scale_escape_qualified",
        "selected", "selected_role", "selection_shortfall",
        "evidence_channel", "selection_basis", "structural_coverage",
        "operator_template", "generated", "run_support", "type_support",
        "feasibility_rate", "accepted_rate", "improvement_rate",
        "distance_reduction_rate", "joint_positive_rate", "basin_escapes",
        "basin_escape_run_support", "basin_escape_run_rate", "required_support",
        "required_run_support", "required_type_support", "required_run_prevalence",
    ])
    write_report(
        output / "trajectory_grammar_report.md", aggregate_files,
        trajectory_files, ignored_files, actual, corrections, basin, candidates,
        args.stagnation_window, args.min_generated_support,
        args.min_run_support, args.min_type_support,
        args.min_neighborhoods, args.max_neighborhoods,
        args.large_scale_min_required_prevalence,
        args.large_scale_min_required_types,
        args.large_scale_min_median_routes,
    )


if __name__ == "__main__":
    main()
