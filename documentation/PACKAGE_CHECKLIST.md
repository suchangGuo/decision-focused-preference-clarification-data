# Public Package Checklist

## Metadata

- [x] Replace author names in `CITATION.cff`, `LICENSE-DATA.md`, and
      `LICENSE-SCRIPTS`.
- [ ] Add each author's ORCID to `CITATION.cff` where available.
- [x] Replace the GitHub repository URL.
- [ ] Add the release date and archived DOI.
- [ ] Add the final article DOI under `preferred-citation` after publication.

## Scientific content

- [x] Add frozen test-instance snapshots and a data dictionary.
- [x] Add the four preference-parameter calibration records.
- [x] Add the final DSP-VNS configuration and random seeds.
- [x] Add the final offline trajectory-driven neighborhood-design materials.
- [x] Add the final small-, medium-, and large-scale algorithm results.
- [x] Add the final Section 6.4-6.6 mechanism-validation results.
- [x] Add one clean source-data file for every reported table and data figure.
- [x] Add the experimental protocol and computational environment.
- [x] Add a manuscript-to-file crosswalk.
- [x] Generate a SHA-256 file manifest.

## Release quality control

- [x] Confirm that every released experiment corresponds to the frozen
      manuscript version.
- [x] Confirm that each result file has a documented role in a manuscript
      table, figure, calibration step, or validation analysis.
- [x] Sanitize logs by removing local paths, usernames, credentials, and
      machine-specific temporary information.
- [x] Confirm that third-party materials are identified in
      `THIRD_PARTY_NOTICES.md`.
