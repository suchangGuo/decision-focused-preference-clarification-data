# Figure contract

- Core conclusion: Increasing interaction cost moves the stopping boundary toward earlier cost-aware termination, leaving more unresolved ambiguity and higher decision risk.
- Figure archetype: quantitative grid delivered as three independent single-column figures.
- Target/output: EJOR-style journal figures; editable SVG and PDF, plus PNG and 600 dpi TIFF.
- Backend: Python/Matplotlib only.
- Final size: 89 mm × 64 mm for the composition figure and 178 mm × 64 mm for each horizontal two-panel trend figure.
- Evidence hierarchy:
  - Figure 1: terminal-state composition.
  - Figure 2: clarification depth and remaining ambiguity.
  - Figure 3: MMR and realized regret.
- Source data: `interaction_cost_summary.csv`.
- Statistics: exact probability enumeration; no sampling error bars are applicable.
- Reviewer risks: avoid dual axes, preserve the true spacing of interaction-cost levels, and keep exact values traceable to the source CSV.

