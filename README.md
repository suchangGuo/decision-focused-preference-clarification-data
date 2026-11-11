# Computational Data and Experimental Records

This repository contains the computational data and experimental records for
the study:

> *Does More Preference Information Lead to Better Actions? Decision-Focused
> Preference Clarification in Time-Critical Combinatorial Optimization*

## Scope

The public package is designed to support verification of the numerical
results reported in the article. It contains the final test instances,
parameter-calibration records, frozen experimental configurations, raw and
processed results, and source data for the reported tables and figures.

Data-processing and figure-generation scripts are provided in
`analysis_scripts` under the terms stated in `LICENSE-SCRIPTS`.

## Repository contents

```text
instances/                  Frozen node, level, travel-time, and endurance data
parameter_calibration/      Independent calibration records for preference parameters
configurations/             Frozen settings and random seeds
neighborhood_design/        Offline search trajectories and identified neighborhoods
algorithm_validation/       Exact benchmarks, stochastic runs, and C2PR comparisons
mechanism_validation/       Data for Sections 6.4--6.6
source_data/                Clean table and figure source files
analysis_scripts/           Data-reduction and figure-generation scripts
documentation/              Protocol, data dictionary, environment, and crosswalk
```

Start with `documentation/MANUSCRIPT_CROSSWALK.md` to locate the materials
supporting a specific section, table, or figure. Variable definitions are
given in `documentation/DATA_DICTIONARY.md`, and file integrity can be checked
against `SHA256SUMS.txt`.

The instance snapshots contain all numerical inputs needed to inspect the
reported test cases without regenerating them from the source benchmark.

## Citation

Citation metadata are provided in `CITATION.cff`. After the repository is
archived, cite the version-specific DOI recorded in that file.

## Licensing

- Data and experimental materials: see `LICENSE-DATA.md`.
- Data-processing and figure-generation scripts: see `LICENSE-SCRIPTS`.
- Third-party materials and software notices: see
  `THIRD_PARTY_NOTICES.md`.

## Release metadata

Before the archived release, add available ORCID records and the
version-specific archive DOI to `CITATION.cff`.
