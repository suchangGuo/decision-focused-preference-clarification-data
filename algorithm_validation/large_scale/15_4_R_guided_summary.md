# 15-4-R：C2引导预算3、触发阈值60的五次复测

## Configuration

- `MaximumIterations = 400`
- `MaximumNoImprovementIterations = 400`
- `CandidatesPerNeighborhood = 20`
- `FrontierCoverageStagnationFraction = 0.15`（阈值60）
- `RobustRestartStagnationFraction = 0.15`（阈值60）
- `FrontierCoverageMaximumCount = 3`
- `RobustRestartMaximumCount = 3`
- `FrontierCoverageCandidatePoolSize = 5`
- `RobustPathRelinkingMaximumSteps = 8`
- `RobustPathRelinkingCandidatesPerStep = 6`
- Algorithm seeds: `2026110301`–`2026110305`
- Exact objective: `0.1563889788`

本轮仅相对于原400×20配置恢复绝对触发阈值60，并将非鲁棒前沿覆盖和鲁棒C2引导的每子问题上限由2提高到3；候选池与路径重联深度保持不变。

## Per-run results

| Run | Seed | Objective | Gap (%) | Time (s) | T | Q | C1 | C2 | C3 | Scale passes | Frontier restarts | Path relinking (success/attempt) | Robust restarts | Feasible |
| ---: | ---: | --------: | ------: | -------: | -: | -: | -: | -: | -: | -----------: | ----------------: | -------------------------------: | --------------: | :------: |
| 1 | 2026110301 | 0.1648495777 | 5.40997131 | 159.177119 | 47.931996 | 10.825163 | 171665 | 52 | 5 | 1 | 12 | 3/3 | 3 | Yes |
| 2 | 2026110302 | 0.1589304546 | 1.62509902 | 295.245323 | 47.793294 | 10.834411 | 315151 | 49 | 9 | 3 | 24 | 1/3 | 3 | Yes |
| 3 | 2026110303 | 0.1610412236 | 2.97479072 | 158.447733 | 47.886621 | 10.834411 | 170440 | 42 | 5 | 1 | 12 | 2/3 | 3 | Yes |
| 4 | 2026110304 | 0.1563889805 | 0.00000110 | 225.583492 | 47.793294 | 10.842859 | 241397 | 50 | 7 | 2 | 18 | 2/3 | 3 | Yes |
| 5 | 2026110305 | 0.1660699849 | 6.19033781 | 236.413598 | 46.981300 | 10.749630 | 241327 | 37 | 7 | 2 | 18 | 2/3 | 3 | Yes |

## Aggregate comparison

| Configuration | Avg. Obj. | Best Obj. | Avg. Time (s) | Max Time (s) | Gap (%) | CV (%) | Exact hits |
| ------------ | --------: | --------: | ------------: | -----------: | ------: | -----: | ---------: |
| 20×300, trigger60, guide2 | 0.16557 | 0.15639 | 165.21170 | 214.48276 | 5.86749 | 7.30556 | 2/5 |
| 20×400, trigger80, guide2 | 0.16929 | 0.16234 | 255.48103 | 304.41562 | 8.25164 | 3.97572 | 0/5 |
| 20×400, trigger60, guide3 | 0.16146 | 0.15639 | 214.97345 | 295.24532 | 3.24004 | 2.49732 | 1/5 |

Relative to the original 400×20 configuration, the expanded C2 budget reduced the average gap from 8.25164% to 3.24004%, reduced CV from 3.97572% to 2.49732%, and reduced average runtime from 255.48103 s to 214.97345 s. Four of five paired seeds improved; one deteriorated. The configuration remained approximately 52.5 times faster than the `11279.403933 s` exact CPLEX chain.

All runs exhausted the third robust C2-guidance allowance. Path-relinking success varied from one to three attempts, confirming that the previous maximum count of two was a binding search-budget constraint rather than an inactive parameter.

## Artifacts

- Raw log: `large_15_4_R_fixedpoint_400x20_c2budget3_trigger60_5runs_raw.log`
- Isolated binary: `model/assistant/bin/C2Budget3Trigger60Trial/assistant.exe`

The current source retains this 400×20, trigger60, guide3 configuration pending final freezing and documentation updates.
