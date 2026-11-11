# Offline trajectory-driven neighborhood design report

## Data boundary

- Full signature-aggregate files: 15
- Selected-node trajectory files: 15
- Ignored non-input CSV files: 0
- Basin-escape stagnation window: 20 iterations
- Minimum generated support: 10
- Minimum independent-run support: 2
- Minimum spatial-type support: 2
- Requested frozen family count: 3--4
- Large-scale escape minimum correction prevalence: 0.50
- Large-scale escape minimum type support: 2
- Large-scale escape minimum median affected routes: 3.00

All rates below use untruncated signature aggregates.  Trajectory rows are not
used as denominators because rejected candidates are retained on a bounded
(objective, distance) frontier.  Exact solutions are used only for offline
distance labeling, and the resulting neighborhood set must be frozen before
held-out algorithm evaluation.

## Actual transition grammar

| family | generated | run_support | type_support | feasibility_rate | accepted_rate | improvement_rate | distance_reduction_rate | joint_positive_rate |
|---|---|---|---|---|---|---|---|---|
| coupled_route_level | 212 | 15 | 3 | 1.0000 | 0.0000 | 0.0000 | 0.1321 | 0.0000 |
| coupled_topology_level | 537 | 11 | 3 | 1.0000 | 0.0019 | 0.0037 | 0.3203 | 0.0037 |
| cross_route_reassignment | 33776 | 15 | 3 | 1.0000 | 0.0039 | 0.0039 | 0.0899 | 0.0023 |
| level_reallocation | 19185 | 15 | 3 | 1.0000 | 0.0459 | 0.0459 | 0.2779 | 0.0218 |
| multi_route_reconstruction | 203 | 14 | 3 | 1.0000 | 0.0000 | 0.0000 | 0.0493 | 0.0000 |
| route_topology | 12119 | 15 | 3 | 1.0000 | 0.0035 | 0.0035 | 0.0649 | 0.0026 |

## RequiredCorrection grammar

For explicit RequiredCorrection events the target is the exact solution;
therefore the required components are read from the event's transformation
signature (gA, gE, gLplus + gLminus, gR), not from the target's zero d-fields.

| family | required_support | required_run_support | required_type_support | required_run_prevalence | median_required_dA | median_required_dE | median_required_dL | median_required_dR |
|---|---|---|---|---|---|---|---|---|
| coupled_route_level | 324 | 15 | 3 | 1.0000 | 2.0000 | 4.0000 | 5.0000 | 3.0000 |
| coupled_topology_level | 82 | 9 | 3 | 0.6000 | 0.0000 | 2.0000 | 4.0000 | 2.5000 |
| cross_route_reassignment | 2 | 2 | 1 | 0.1333 | 2.0000 | 8.0000 | 0.0000 | 3.0000 |
| level_reallocation | 421 | 14 | 3 | 0.9333 | 0 | 0 | 4 | 2 |
| multi_route_reconstruction | 306 | 14 | 3 | 0.9333 | 3.0000 | 8.0000 | 6.0000 | 4.0000 |
| route_topology | 4 | 4 | 2 | 0.2667 | 0.0000 | 2.0000 | 0.0000 | 1.0000 |

## Basin escapes

| family | basin_escapes | basin_escape_run_support | basin_escape_type_support | median_stagnation_length |
|---|---|---|---|---|
| coupled_route_level | 3 | 3 | 1 | 32 |
| coupled_topology_level | 4 | 2 | 1 | 53.0000 |
| level_reallocation | 3 | 3 | 2 | 26 |
| multi_route_reconstruction | 1 | 1 | 1 | 33 |

## Frozen candidate neighborhood families

Selection is a rule chain rather than a weighted score: replication thresholds,
separate Pareto screens for demonstrated transitions and RequiredCorrection,
then distinct assignment, topology, and level-refinement roles.  Multi-route
reconstruction is admitted as a fourth, large-scale escape role only when its
RequiredCorrection prevalence, type support, and median affected-route count
meet the declared thresholds.  No redundant family is added merely to reach a
requested count.  A family supported only by RequiredCorrection is a design
requirement, not demonstrated search effectiveness.

| family | selected_role | evidence_channel | selection_basis | structural_coverage | operator_template |
|---|---|---|---|---|---|
| coupled_route_level | assignment_reallocation;basin_escape | actual+required | required_pareto;actual+required | A+E+L+R | cross-route transfer with paired level rebalance |
| coupled_topology_level | route_topology | actual+required | actual_pareto;actual+required | E+L | route-segment change with paired level rebalance |
| level_reallocation | level_reallocation | actual+basin+required | actual_pareto;actual+basin+required | L | reallocate reconnaissance levels under a fixed route plan |
| multi_route_reconstruction | large_scale_escape | actual+required | actual+required | A+E+R | partial multi-route destroy-and-rebuild |

## Interpretation boundary

1. Treat aggregate counts as the only source of generation and success rates.
2. Treat RequiredCorrection as structural demand, not an observed successful move.
3. Treat retained rejected candidates as acceptance-barrier diagnostics only.
4. Freeze the selected 3--4 operators before testing unseen seeds or instances.
5. Report held-out performance separately from this operator-design experiment.
