# Data Dictionary

## Instance snapshots

`instances/instance_registry.csv` identifies every frozen instance. `N`, `U`,
and `L` denote the numbers of affected regions, available UAVs, and
reconnaissance levels; `H` is the per-UAV endurance limit in minutes.

Each instance directory contains:

- `nodes_and_levels.csv`: node identifier, source Solomon customer identifier,
  coordinates, reconnaissance level, local task time, and information gain.
  The depot is recorded once with level 0.
- `travel_times.csv`: directed origin-destination flight times in minutes,
  including the depot and all affected-region nodes.

## Algorithm-validation records

Raw `.log` files retain the run configurations, seeds, objectives, solution
times, feasibility flags, cache statistics, and restart statistics emitted by
the experiment runners. Companion `.md` files record the frozen summaries used
to construct the manuscript tables.

`source_data/tables/table6_algorithm_validation.csv` reports the exact-solver
benchmark and five-run DSP-VNS summaries. `table7_C2PR_ablation.csv` reports
the paired large-instance comparison. Lower objective values are preferred.
For Table 6, `gap_percent` equals 100 times the difference between the average
DSP-VNS objective and the exact objective, divided by the exact objective. For
Table 7, `improvement_percent` equals 100 times the difference between the
baseline and C2PR average objectives, divided by the baseline objective;
positive values favor C2PR. `cv_percent` is the coefficient of variation over
the five stochastic runs.

## Offline trajectory-driven neighborhood design

Files ending in `_trajectory.csv` contain recorded search states. Files ending
in `_signature_aggregate.csv` aggregate transformation signatures observed in
each run. `neighborhood_design/analysis` contains the cross-run statistics and
the frozen neighborhood set derived from those trajectories.

## Mechanism-validation records

- `action_regions`: exact action regions and switching boundaries.
- `equal_width_windows`: 555 equal-width ambiguity-window observations and
  their category summaries.
- `boundary_value`: boundary-level decision consequences and clarification
  value.
- `query_objectives`: paired results for preference-space contraction and
  decision-oriented query selection.
- `stopping_boundaries`: trajectory terminal states and stopping categories.
- `interaction_cost`: stopping outcomes under four interaction-cost levels.

Processed CSV headers are self-describing. Corresponding Markdown reports
define any experiment-specific aggregation or probability weighting.
