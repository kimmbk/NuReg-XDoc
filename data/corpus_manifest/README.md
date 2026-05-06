# Corpus Manifest

The 200-document retrieval corpus used by NuReg-XDoc Section 4 experiments
is enumerated here. NRC PDFs themselves are not redistributed; users
retrieve them from the NRC ADAMS public document system using the
`nrc_adams_accession` and `source_url` columns.

| File | Rows | Role |
|------|-----:|------|
| `evidence_documents.csv` | 156 | Documents that appear in at least one of the 938 released evidence chains. |
| `distractor_documents.csv` | 44 | Documents drawn from the same regulatory hierarchy that are NOT cited by any released query. |

Columns:

- `doc_id` — canonical document identifier (used in `data/nureg-xdoc-queries.json` evidence chains for evidence documents).
- `doc_type` — `10CFR` / `SRP` / `DSRS` / `RG`.
- `reference` — human-readable section identifier (e.g., `SRP 2.3.1`, `RG 1.70`).
- `role` — `evidence` or `distractor`.
- `nrc_adams_accession` — NRC ADAMS accession number where applicable.
- `source_url` — direct URL to the NRC ADAMS object.
- `filename` — original PDF filename used by the construction pipeline.

For `10 CFR Part 50`, retrieval is from the e-CFR system rather than
ADAMS; see `DATA_SOURCES.md` in the parent directory.

## Document revisions

A regulatory reference (e.g., `RG 1.70`) may correspond to multiple
historical PDF revisions in the retrieval corpus. In this case the
manifest contains one row per revision, all sharing the same `doc_id`
and `reference`, with distinct `nrc_adams_accession` and `filename`
values. Six references in v1.0.0 have multiple revisions:

| Reference | Role | Number of revisions |
|---|---|---:|
| RG 1.70 | distractor | 5 |
| SRP 15.4.8 | evidence | 2 |
| SRP 2.1.2 | distractor | 2 |
| SRP 3.4.1 | distractor | 2 |

Evaluation against the evidence chain `doc_id` is reference-level: any
indexed revision of the cited reference counts as a correct retrieval.
