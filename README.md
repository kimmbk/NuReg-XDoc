# NuReg-XDoc v1

A Cross-Doctype Regulatory QA Benchmark with Document-Grounded
Reasoning Paths for KG-Augmented RAG.

| | |
|---|---|
| Version | 1.0.0 |
| Release date | 2026-05-03 |
| DOI | 10.5281/zenodo.19915566 |
| Code repository | https://github.com/kimmbk/NuReg-XDoc |
| Authors | Bokyeong Kim, Hyewon Lee, Yonggyun Yu (Corresponding) |
| Data license | CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) |
| Code license | MIT (see `LICENSE`) |

## Overview

NuReg-XDoc is a benchmark for cross-document, cross-doctype
question answering over the U.S. nuclear regulatory hierarchy.
The deposit contains three coordinated artifacts:

1. **Queries.** 938 review queries derived from NRC Requests for
   Additional Information (RAI). Each query carries an ordered
   evidence chain with section anchors, supporting documents,
   and a reference type drawn from a three-valued taxonomy.
2. **Reference graph.** A document-level RDF/OWL knowledge graph
   over 135 regulatory documents and 392 typed inter-document
   edges. Edges are induced from the evidence chains; every
   released edge is witnessed by at least one chain.
3. **Construction code.** `build_graph.py` rebuilds the reference
   graph from the query JSON bit-identically.

The benchmark is released as a single evaluation set. Users may
construct task-specific train/dev/test splits as needed.

## Directory layout

```
NuReg-XDoc-1.0.0/
├── README.md                              # this file
├── LICENSE                                # MIT (data licensed CC BY 4.0)
├── CITATION.cff                           # canonical citation
├── DATA_SOURCES.md                        # NRC source URLs and copyright
├── croissant.json                         # Croissant ML metadata (dataset)
├── void.ttl                               # VoID metadata (RDF graph)
├── data/
│   └── nureg-xdoc-queries.json            # 938 query records
├── graph/
│   ├── SCHEMA.md                          # graph schema reference
│   ├── nureg-xdoc-ontology.ttl            # OWL classes and properties
│   ├── nureg-xdoc-instances.ttl           # 135 document nodes, 392 edges
│   ├── nureg-xdoc-graph.ttl               # ontology + instances merged
│   ├── nureg-xdoc-nodes.csv               # node dump
│   ├── nureg-xdoc-edges.csv               # edge dump
│   └── nureg-xdoc-cooccurrence-edges.csv  # chain-level co-occurrence
└── code/
    └── build_graph.py                     # reference graph constructor
```

## Dataset statistics

Computed from `data/nureg-xdoc-queries.json`.

| Field | Value |
|---|---|
| Total queries | 938 |
| Cross-document queries | 917 / 938 (97.8%) |
| Cross-doctype queries | 911 / 938 (97.1%) |
| Average documents per query | 3.32 |
| Average supporting facts per query | 3.32 |
| Average answer length (words) | 293 |
| Judge pass rate | 100% |
| Judge score (mean) | 4.75 / 5.0 |

### Difficulty

| Difficulty | Count | Share |
|---|---:|---:|
| Easy | 285 | 30.4% |
| Medium | 272 | 29.0% |
| Hard | 381 | 40.6% |

### Question type

| Type | Count |
|---|---:|
| bridge | 863 |
| comparison | 48 |
| single_doc_factoid | 21 |
| regulatory_chain | 6 |

### Hop depth

| n_hops (max reference-type transition depth) | Count |
|---|---:|
| 0 | 21 |
| 1 | 781 |
| 2 | 123 |
| 3 | 13 |

### Reference-type taxonomy

The taxonomy formalises the citation structure of regulatory
documents into three values plus a null start marker.

| reference_type | Transition pattern | Regulatory meaning | Count |
|---|---|---|---:|
| `normative_basis` | SRP/DSRS to 10 CFR | Review standard cites a legal provision (CFR / GDC) | 873 |
| `methodology_guidance` | SRP/DSRS to RG, 10 CFR to RG | Requirement cites an accepted methodology (Regulatory Guide) | 897 |
| `lateral_cross_reference` | SRP to SRP, DSRS to DSRS | Cross-reference between sections of the same role | 403 |
| `null` | hop = 0 | Chain starting point, no inbound transition | 938 |

68.4% of queries require evidence chains spanning two or more
reference types.

### Source split

| Source | Queries | Reactor design |
|---|---:|---|
| NuScale | 693 | NuScale Small Modular Reactor |
| Levy | 245 | Levy County (Westinghouse AP1000) |

## Query schema

Top-level keys:

```json
{
  "metadata": { ... },
  "data": [ <QueryRecord>, ... ]
}
```

Each `QueryRecord`:

| Field | Type | Description |
|---|---|---|
| `query_id` | string | `{source}_{rai_index}_{difficulty}_{within_rai_index}` |
| `query` | string | Natural-language question |
| `difficulty` | enum | `easy` / `medium` / `hard` |
| `question_type` | enum | `bridge` / `comparison` / `single_doc_factoid` / `regulatory_chain` |
| `n_hops` | int | Number of reference transitions in the evidence chain |
| `answer` | string | Reference answer |
| `evidence_chain` | array | Ordered evidence chain (see below) |
| `judge_score` | float | LLM-judge faithfulness score, 0 to 5 |
| `judge_verdict` | enum | `pass` / `fail` |
| `metadata.source` | enum | `nuscale` / `levy` |
| `metadata.original_rai_number` | string | NRC RAI identifier |
| `metadata.section_number` | string | RAI section anchor |
| `metadata.target_concepts` | array | Concept tags (annotator-supplied) |
| `metadata.extracted_refs` | array | Document references parsed from the RAI |
| `metadata.confidence` | float | Pipeline confidence, 0 to 1 |

Each entry in `evidence_chain`:

| Field | Type | Description |
|---|---|---|
| `hop` | int | Position in the evidence chain (0-indexed) |
| `doc_id` | string | Canonical document identifier |
| `doc_type` | enum | `10CFR` / `SRP` / `DSRS` / `RG` |
| `section` | string | Section/clause anchor inside `doc_id` (e.g., "Appendix A, Criterion 2") |
| `evidence_text` | string | Verbatim cited passage |
| `role` | enum | Functional role of the fact in the chain |
| `action` | string | Reasoning step description |
| `reference_type` | enum or null | Transition type (see taxonomy above); `null` for hop 0 |
| `has_table_reference` | bool | Whether the passage references a table |

## Reference graph

The reference graph follows the schema documented in
`graph/SCHEMA.md`. Summary:

- 135 document nodes (SRP 63, RG 39, DSRS 32, 10 CFR 1)
- 392 distinct directed typed edges
- 2,173 chain-occurrence weight (sum of edge weights)
- Reuse ratio: NB 10.4, MG 5.6, LCR 2.7

## Reproducing the reference graph

```bash
# requires Python 3.9+, no external dependencies (stdlib only)
python code/build_graph.py \
    --input data/nureg-xdoc-queries.json \
    --outdir graph/
```

The script writes five files in `graph/`: `ontology.ttl`,
`instances.ttl`, `nodes.csv`, `edges.csv`, and
`cooccurrence_edges.csv`. The shipped deposit additionally includes
`nureg-xdoc-graph.ttl` (the union of `ontology.ttl` and
`instances.ttl`) and renames each file with the `nureg-xdoc-`
prefix; output content hashes match the corresponding shipped
files.

## FAIR metadata

| Standard | File | Scope |
|---|---|---|
| Croissant 1.0 | `croissant.json` | Tabular ML dataset description for the query JSON |
| W3C VoID | `void.ttl` | RDF dataset description for the reference graph |

## Quality assurance

Quality is verified at three levels.

1. **Pipeline judge.** A GPT-4.1 judge filters unsupported
   extractions in Phase 4 of the construction pipeline.
2. **Evidence-chain agreement.** A 100-query stratified sample
   of evidence chains was independently annotated by two domain
   experts. Cohen's κ = 0.88.
3. **Reference-type agreement.** A 49-edge stratified sample
   validates the reference-type taxonomy. Cohen's κ = 0.94.

Annotation guidelines and raw labels are not part of this deposit
and are available from the corresponding author upon request.

## Citation

If you use NuReg-XDoc, please cite the dataset using the entry
below. See `CITATION.cff` for the canonical machine-readable form.

```bibtex
@dataset{kim2026nuregxdoc_data,
  author    = {Kim, Bokyeong and Lee, Hyewon and Yu, Yonggyun},
  title     = {NuReg-XDoc: A Cross-Doctype Regulatory QA Benchmark (v1.0.0)},
  year      = {2026},
  publisher = {Zenodo},
  version   = {1.0.0},
  doi       = {10.5281/zenodo.19915566}
}
```

## Source documents

NRC PDFs are not redistributed in this deposit. Source URLs and
copyright status are in `DATA_SOURCES.md`.

## Changelog

### v1.0.0 (2026-05-03)

Initial public release on Zenodo, accompanying the ISWC 2026
paper. The deposit consolidates the schema and artifacts
developed across internal pre-release iterations.

- 938 review queries with ordered evidence chains, derived from
  991 NRC RAI documents through a four-phase extraction pipeline.
- Document-level reference knowledge graph: 135 nodes, 392 typed
  directed edges (NB, MG, LCR), released as RDF/OWL Turtle plus
  CSV dumps.
- Construction code (`code/build_graph.py`) rebuilds the
  reference graph from the query JSON bit-identically.
- FAIR metadata: Croissant 1.0 dataset description and W3C VoID
  RDF dataset description.
- Dual licensing: CC BY 4.0 for data, MIT for code.
