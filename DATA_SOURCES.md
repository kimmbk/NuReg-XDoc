# Data Sources

NuReg-XDoc is constructed from publicly available U.S. Nuclear
Regulatory Commission (NRC) documents. All source documents are
works of the U.S. federal government and are in the public domain
under 17 U.S.C. § 105.

## Document corpus

The benchmark distinguishes three document layers, each used at a
different stage of construction. They are not the same set.

| Layer | Count | Description |
|---|---:|---|
| Full crawl (5 doctypes) | 961 | Internal preprocessing pool used during pipeline development. Includes Federal Register amendments. Not released as a corpus. |
| Released corpus (4 doctypes) | 200 | 156 evidence + 44 distractor documents covering 10 CFR, SRP, DSRS, RG. Used as the retrieval target in paper §3.1 (Table 3). |
| Reference-graph nodes | 135 | Subset of the 156 evidence documents that participates in at least one of the 938 released evidence chains. The remaining 21 evidence documents were cited by an RAI but did not yield a chain edge. |

Per-doctype document occurrences (the number of times each doctype
appears across the 938 query records) are listed below. These are
occurrence counts, not deduplicated document counts.

| Document type | Occurrences | Description |
|---|---:|---|
| 10 CFR | 878 | Code of Federal Regulations, Title 10 (Energy) |
| SRP | 907 | Standard Review Plan (NUREG-0800) |
| DSRS | 407 | Design-Specific Review Standard |
| RG | 919 | Regulatory Guide |

After deduplication the released corpus contains 200 documents and
the reference graph contains 135 unique document nodes (79 unique
sections).

## Query source

The 938 review queries are derived from NRC Requests for
Additional Information (RAI) issued during nuclear power plant
licensing reviews. Two reactor design dockets are used:

| Source | Queries | Reactor design |
|---|---|---|
| NuScale | 693 | NuScale Small Modular Reactor (US600) |
| Levy | 245 | Levy County (Westinghouse AP1000) |

## Public access URLs

| Resource | URL |
|---|---|
| NRC ADAMS public document system | https://adams.nrc.gov/wba/ |
| 10 CFR online | https://www.nrc.gov/reading-rm/doc-collections/cfr/ |
| Standard Review Plan (NUREG-0800) | https://www.nrc.gov/reading-rm/doc-collections/nuregs/staff/sr0800/ |
| Regulatory Guides | https://www.nrc.gov/reading-rm/doc-collections/reg-guides/ |
| NuScale design certification documents | https://www.nrc.gov/reactors/new-reactors/smr/licensing-activities/nuscale.html |
| Levy County combined license documents | https://www.nrc.gov/reactors/new-reactors/large-lwr/levy.html |

## Copyright and redistribution

NRC PDFs themselves are not redistributed in this Zenodo deposit.
Users requiring the source documents should retrieve them from
the URLs above, which provide stable public access. Document
identifiers in the dataset (file paths, section numbers, page
ranges, character offsets) follow the NRC ADAMS accession
numbering scheme to support unambiguous lookup.

## Derived artifacts

The artifacts in this deposit (`nureg-xdoc-queries.json`, the
reference graph TTL/CSV files, and `build_graph.py`) are derived
works produced by the authors. They are released under the
following licenses: dataset and metadata under CC BY 4.0
(https://creativecommons.org/licenses/by/4.0/), and source code
under the MIT License (see `LICENSE`).

## Generation pipeline

Queries and evidence chains were extracted from NRC RAI documents
using GPT-4.1 in a four-phase pipeline (extraction, validation,
chain construction, judge filtering). Two stratified samples
(100 evidence chains, 49 reference-graph edges) were independently
annotated by two domain experts to establish quality bounds
(Cohen's κ = 0.88 and 0.94, respectively). The annotation
guidelines and raw labels are not included in this deposit; they
are available from the corresponding author upon request.
