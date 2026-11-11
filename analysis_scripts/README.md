# Analysis and Figure Scripts

Install the lightweight analysis dependencies with:

```bash
python -m pip install -r analysis_scripts/requirements.txt
```

Run the figure and stopping-summary scripts from the repository root:

```bash
python analysis_scripts/plot_action_region_partition.py
python analysis_scripts/plot_query_objective_mismatch.py
python analysis_scripts/analyze_stopping_boundaries.py
python analysis_scripts/plot_cint_boundary_figures.py
```

Reproduce the offline trajectory aggregation with:

```bash
python analysis_scripts/analyze_trajectory_grammar.py \
  neighborhood_design/trajectory_data \
  --output-dir neighborhood_design/analysis
```

The scripts read only the released CSV files. Figure outputs are written to
`source_data/figures`, while tabular reductions are written to their
corresponding analysis directory.
