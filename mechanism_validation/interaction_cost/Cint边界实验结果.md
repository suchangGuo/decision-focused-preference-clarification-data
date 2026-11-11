# Interaction-cost boundary experiment

## Experimental setting

- Interaction-cost levels: \(C^{\mathrm{int}}\in\{0,0.0047,0.0094,0.0188\}\).
- Formal instances: 15 instances with \(N=9\), \(U=3\), five seeds, and R/C/RC spatial structures.
- Initial ambiguity set: \([0.30,0.70]\).
- Hidden preference positions: \(\{0.1,0.3,0.5,0.7,0.9\}\) within the initial interval.
- Maximum clarification rounds: 5.
- Feedback branches are enumerated exactly. All settings other than \(C^{\mathrm{int}}\) remain unchanged.
- The robust-state cache is shared across cost levels within each physical instance because the robust solution for a given ambiguity set does not depend on the interaction cost.

## Aggregate results

| \(C^{\mathrm{int}}\) | Action-stable (%) | Cost-aware (%) | Resource-constrained (%) | Structural (%) | Mean queries | Remaining width | Mean action regions | Mean MMR | Realized regret | Interaction expenditure | Total decision loss |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.2161 | 8.8723 | 18.7945 | 72.1171 | 3.0000 | 0.12094 | 2.4592 | 0.00702 | 0.00084 | 0.00000 | 0.00084 |
| 0.0047 | 0.0333 | 61.6944 | 0.0000 | 38.2723 | 1.7541 | 0.15743 | 3.0246 | 0.01451 | 0.00166 | 0.00824 | 0.00991 |
| 0.0094 | 0.0000 | 78.5462 | 0.0000 | 21.4538 | 1.3504 | 0.17925 | 3.3578 | 0.02130 | 0.00313 | 0.01269 | 0.01583 |
| 0.0188 | 0.0000 | 81.1916 | 0.0000 | 18.8084 | 1.1624 | 0.18989 | 3.5486 | 0.02511 | 0.00439 | 0.02185 | 0.02624 |

Here, total decision loss is the sum of realized regret and cumulative interaction expenditure within each cost scenario.

## Internal interpretation

The stopping mechanism responds monotonically to the interaction-cost boundary. As \(C^{\mathrm{int}}\) increases, the mean number of queries decreases, while the remaining ambiguity width, the number of retained action regions, MMR, and realized regret increase. Resource-constrained termination appears only at zero cost, showing that a positive interaction cost becomes binding before the five-round limit in the tested setting.

The calibrated value \(C^{\mathrm{int}}=0.0094\) lies between the low-cost deep-clarification regime and the high-cost early-stopping regime. Relative to 0.0047, it reduces the mean query count from 1.7541 to 1.3504 and raises the cost-aware stopping share from 61.6944% to 78.5462%. Doubling the cost to 0.0188 produces a smaller additional change in stopping share, from 78.5462% to 81.1916%, indicating that the stopping response is approaching saturation.

Interaction cost is treated as an exogenous opportunity cost rather than a tunable algorithmic parameter. Consequently, total decision loss should not be minimized across rows to select a preferred cost level: changing \(C^{\mathrm{int}}\) changes the decision environment itself. The experiment is used to verify that the stopping boundary adjusts coherently to different interaction-cost environments and that the calibrated baseline does not induce either persistent clarification or universal immediate stopping.

## Validation

- Terminal probability mass equals one for every cost-instance-hidden-preference combination.
- All reported probability, width, MMR, and regret values are finite.
- The \(C^{\mathrm{int}}=0.0094\) results reproduce the original Section 6.6 baseline exactly.
- Formal run: 2,552 terminal leaf records; runtime 2,682.48 s.
