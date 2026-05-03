# Data Sources

NuReg-XDoc is constructed from publicly available U.S. Nuclear
Regulatory Commission (NRC) documents. All source documents are
works of the U.S. federal government and are in the public domain
under 17 U.S.C. § 105.

## Document corpus

The corpus comprises 961 PDFs across four document types in the
U.S. nuclear regulatory hierarchy.

| Document type | Count | Description |
|---|---|---|
| 10 CFR | 878 | Code of Federal Regulations, Title 10 (Energy) |
| SRP | 907 | Standard Review Plan (NUREG-0800) |
| DSRS | 407 | Design-Specific Review Standard |
| RG | 919 | Regulatory Guide |

Counts above reflect document occurrences across the 938 query
records; the corpus contains 135 unique documents and 79 unique
sections after deduplication.

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
licenses stated in `LICENSE-DATA` (CC BY 4.0) and `LICENSE-CODE`
(MIT).

## Generation pipeline

Queries and evidence chains were extracted from NRC RAI documents
using GPT-4.1 in a four-phase pipeline (extraction, validation,
chain construction, judge filtering). Two stratified samples
(100 evidence chains, 49 reference-graph edges) were independently
annotated by two domain experts to establish quality bounds
(Cohen's κ = 0.88 and 0.94, respectively). The annotation
guidelines and raw labels are not included in this deposit; they
are available from the corresponding author upon request.
