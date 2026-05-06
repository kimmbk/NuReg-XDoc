# NuReg-XDoc v1

A Cross-Doctype Regulatory QA Benchmark with Document-Grounded
Reasoning Paths for KG-Augmented RAG.

| | |
|---|---|
| Version | 1.0.0 |
| Release date | 2026-05-07 |
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

The benchmark is released as a single evaluation set. The companion
paper does not require a fixed train/dev/test split; users may
construct task-specific splits as needed.

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
│   ├── nureg-xdoc-queries.json            # 938 query records
│   └── corpus_manifest/                   # 200-document retrieval corpus manifest
│       ├── README.md
│       ├── evidence_documents.csv         # 156 evidence documents
│       └── distractor_documents.csv       # 44 distractor documents
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

### Chain length and reference-type transition depth

The dataset exposes two distinct depth measures. They are not
interchangeable.

| Measure | Definition | Where it appears |
|---|---|---|
| `chain_length` | Number of evidence passages in the chain (length of `evidence_chain`). | Paper Table 5(b) "Hop depth" column. Range 1-5. |
| `n_hops` | Maximum reference-type transition depth along the chain (cap at 3). | `n_hops` field of each query record. Range 0-3. |

#### Chain length distribution (paper Table 5(b))

| chain_length | Count | Share |
|---:|---:|---:|
| 1 | 21 | 2.2% |
| 2 | 264 | 28.1% |
| 3 | 278 | 29.6% |
| 4 | 147 | 15.7% |
| 5+ | 228 | 24.3% |

Mean chain length: 3.32.

#### `n_hops` distribution (record field)

| `n_hops` | Count |
|---:|---:|
| 0 | 21 |
| 1 | 781 |
| 2 | 123 |
| 3 | 13 |

### Reference-type taxonomy

The taxonomy formalises the citation structure of regulatory
documents into three values plus a null start marker.

| reference_type | Transition pattern | Regulatory meaning | Distinct edges | Chain occurrences |
|---|---|---|---:|---:|
| `normative_basis` | SRP/DSRS to 10 CFR | Review standard cites a legal provision (CFR / GDC) | 84 | 873 |
| `methodology_guidance` | SRP/DSRS to RG, 10 CFR to RG | Requirement cites an accepted methodology (Regulatory Guide) | 160 | 897 |
| `lateral_cross_reference` | SRP to SRP, DSRS to DSRS | Cross-reference between sections of the same role | 148 | 403 |
| `null` | hop = 0 | Chain starting point, no inbound transition | -- | 938 |

`Distinct edges` counts unique directed typed edges `(src, dst, ref_type)`
and matches `nureg-xdoc-edges.csv` (392 rows total). `Chain occurrences`
sums the `weight` column across edges of each type and matches the
chain-occurrence weight reported in `void.ttl` (2,173 total). The two
columns correspond to the Distinct / Weight split in Table 4 of the paper.

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
| `n_hops` | int | Pipeline-recorded reference-type transition depth (range 0--3); `len(evidence_chain)` gives the supporting-fact count used as Hop depth in the paper |
| `answer` | string | Reference answer |
| `evidence_chain` | array | Ordered evidence chain (see below) |
| `judge_score` | float | LLM-judge faithfulness score, 0 to 5 |
| `judge_verdict` | enum | `pass` / `fail` |
| `metadata.source` | enum | `nuscale` / `levy` |
| `metadata.original_rai_number` | string | NRC RAI identifier |
| `metadata.section_number` | string | RAI section anchor |
| `metadata.target_concepts` | array | Concept tags (annotator-supplied) |
| `metadata.extracted_refs` | array | Document references parsed from the RAI |
| `metadata.confidence` | enum | Pipeline confidence label: `high` (936) / `medium` (2) |

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
`graph/SCHEMA.md`. The 135 nodes are the subset of the 200-document
released corpus (156 evidence + 44 distractor; see `DATA_SOURCES.md`)
that participates in at least one of the 938 released evidence chains.
Summary:

- 135 document nodes (SRP 63, RG 39, DSRS 32, 10 CFR 1)
- 392 distinct directed typed edges
- 2,173 chain-occurrence weight (sum of edge weights)
- Reuse ratio: NB 10.4, MG 5.6, LCR 2.7

The ontology IRI <https://regrag.org/ontology> is a stable
identifier; the namespace is currently not dereferenceable. The
canonical Turtle file is `graph/nureg-xdoc-ontology.ttl` in this
deposit (also archived under DOI 10.5281/zenodo.19915566).

### Document revisions in the retrieval corpus

The 200-PDF retrieval corpus indexes individual PDF revisions, while
the evidence chains and the reference graph index unique document
references (e.g., `RG 1.70`). Some references therefore appear in
multiple manifest rows because the corpus contains several historical
revisions of the same document; for example `RG 1.70` appears in five
distractor rows with five distinct ADAMS accession numbers, and
`SRP 15.4.8` appears in two evidence rows. Retrievers index each PDF
separately; ground-truth evaluation against the chain `doc_id`
(reference-level) treats any revision of the cited reference as a
correct retrieval.

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
   extractions in Phase 4 of the construction pipeline. The judge
   agrees with two human annotators at Cohen's κ = 0.78 on a 50-item
   calibration set.
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
copyright status are in `DATA_SOURCES.md`. The 938 queries trace to
426 unique source RAIs that survived the four-phase construction
pipeline (an initial pool of 991 RAIs is reduced to 509 by Phase 1
filtering; subsequent rewrite, issue split, chain extraction, and
judge filtering produce the released set).

## Changelog

### v1.0.0 (2026-05-07)

Initial public release for ISWC 2026 Resources Track submission.

- README: split the prior "Hop depth" table into two distinct
  measures, `chain_length` (1-5) and `n_hops` (0-3), to match the
  paper's Table 5(b) "Hop depth" column without ambiguity.
- README: extended the reference-type taxonomy table with both
  `Distinct edges` (matching `nureg-xdoc-edges.csv`, 392 rows)
  and `Chain occurrences` (matching `void.ttl`, 2,173 total).
- README: clarified that the 135 reference-graph nodes are a
  subset of the 200-document released corpus.
- README: added a one-line note on ontology IRI use as a stable
  identifier (the namespace is not dereferenceable; the canonical
  Turtle file is the deposit's `graph/nureg-xdoc-ontology.ttl`).
- DATA_SOURCES: replaced the prior single corpus table with a
  three-layer hierarchy table (full crawl 961 / released corpus
  200 / reference-graph nodes 135), and relabelled the doctype
  table column from "Count" to "Occurrences".
