# Experimental Protocol

## Instance construction

R, C, and RC spatial structures use the coordinate relations of Solomon R101,
C101, and RC101. Coordinates are converted at 0.20 km per unit and travel
times assume a UAV cruising speed of 60 km/h. The frozen node, level, and
travel-time values are supplied directly in `instances`; no regeneration is
required for result verification.

## Algorithm validation

Each exact benchmark is solved once. DSP-VNS is run five times per instance
with the frozen configuration and independent algorithm seeds. The additional
14-4-R series uses seeds 2026110306-2026110310, as documented in the cross-seed
record. Reported objectives are evaluated on the common frozen normalization
scale.

The large-instance C2PR comparison is paired by instance, seed, and search
budget. Dominance-based safe pruning remains active in both variants; the
comparison removes only the C2-guided path-relinking/restart mechanism.

## Mechanism validation

Mechanism-validation experiments use five independent instance seeds. Exact
action-region mapping is followed by equal-width window analysis, boundary
value analysis, query-objective comparison, stopping-boundary classification,
and interaction-cost sensitivity. The detailed aggregation rule for each
experiment is recorded in its companion Markdown report.
