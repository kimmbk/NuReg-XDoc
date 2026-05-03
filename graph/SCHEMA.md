# NuReg-XDoc Document-Level Reference Knowledge Graph — Schema Reference

This document describes the schema and release artifacts of the
`NuReg-XDoc` document-level reference Knowledge Graph (KG). It is the
authoritative reference for Section 3.2 of the paper.

---

## 1. Design rationale

Graph-RAG systems such as HippoRAG, LightRAG, and LGraphRAG build
**entity-level** KGs in which nodes are entities and mentions extracted
from passage text. `NuReg-XDoc` instead builds a **document-level** KG
in which nodes are regulatory documents and edges are typed
inter-document references written into the documents themselves. This
preserves the hierarchical citation structure that regulatory reasoning
depends on, rather than reducing it to entity co-occurrence.

The KG adopts the W3C standards RDF and OWL, and separates the schema
(`nureg-xdoc-ontology.ttl`) from the instance data
(`nureg-xdoc-instances.ttl`). Separation
lets the schema be reused for parallel regulatory benchmarks in other
jurisdictions or domains without re-publishing the dataset.

---

## 2. Release artifacts

| File | Format | Role |
|------|--------|------|
| `nureg-xdoc-ontology.ttl` | W3C OWL / Turtle | Schema definitions. No instance data. |
| `nureg-xdoc-instances.ttl` | RDF / Turtle | 135 document nodes and 392 typed edges that `owl:imports` the ontology. |
| `nureg-xdoc-graph.ttl` | RDF / Turtle | Merged ontology and instances in a single file. |
| `nureg-xdoc-nodes.csv` | CSV | Flat dump: `doc_id, doc_type, query_count, out_degree_weighted, in_degree_weighted`. |
| `nureg-xdoc-edges.csv` | CSV | Flat dump: `src, dst, reference_type, weight, example_query_ids`. |
| `nureg-xdoc-cooccurrence-edges.csv` | CSV | Undirected chain-level co-occurrence edges. Analysis aid, not part of the KG. |

---

## 3. Ontology (`nureg-xdoc-ontology.ttl`)

Namespace: `rrg: <https://regrag.org/ontology#>`.

### 3.1 Class

- `rrg:RegulatoryDocument` — a single regulatory document participating
  in the KG.

### 3.2 Datatype properties

- `rrg:docType` (functional) — enumerated doctype of the document.
  Range restricted by `owl:oneOf` to `{"10CFR", "SRP", "DSRS", "RG"}`.
- `rrg:queryCount` — number of benchmark queries whose evidence chain
  touches the document. `xsd:nonNegativeInteger`.

### 3.3 Object properties

`rrg:references` is the super-property; the three typed sub-properties
are licensed by distinct clause patterns in the source documents.

| Property | Licensing clause | Typical direction |
|----------|------------------|-------------------|
| `rrg:normativeBasis` | "shall comply with ..." | Review / methodology to legal authority |
| `rrg:methodologyGuidance` | "an acceptable method is ..." | Review document to methodology document |
| `rrg:lateralCrossReference` | "see also ..." | Between sections of the same role |

### 3.4 Edge weight

Each typed edge is asserted as a direct triple and reified as an
`rdf:Statement`, with `rrg:weight` recording the number of evidence
chains that traverse the edge. This allows distinct-edge and
chain-occurrence aggregations to share the same KG.

```turtle
doc:SRP_2-3-1 rrg:normativeBasis doc:10_CFR_Part_50 .
_:e123 a rdf:Statement ;
    rdf:subject   doc:SRP_2-3-1 ;
    rdf:predicate rrg:normativeBasis ;
    rdf:object    doc:10_CFR_Part_50 ;
    rrg:weight    5 .
```

---

## 4. Induction from evidence chains

Edges are induced from the Phase-3 evidence chains of the 938 queries.
For every supporting fact $F_j$ with `hop > 0` and a non-null
`reference_type`, a directed typed edge is added from the nearest
preceding fact $F_i$ with `hop = F_j.hop - 1` (fallback: the chain's
`hop = 0` fact) to $F_j$, labelled with $F_j$'s `reference_type`.
Self-loops are dropped. Edge identity is the triple
`(src, dst, reference_type)`; multiple chains touching the same edge
collapse onto a single edge whose weight records the chain-occurrence
count.

The canonical implementation is `build_graph.py` in the release
bundle; re-running it on `nureg-xdoc-queries.json` reproduces
`nureg-xdoc-ontology.ttl` and `nureg-xdoc-instances.ttl`
bit-identically.

---

## 5. Statistics

Computed from `nureg-xdoc-queries.json` (938 queries).

### 5.1 Nodes

- Total: **135** documents.
- By `docType`: SRP **63**, RG **39**, DSRS **32**, 10CFR **1**.

Note: the full corpus contains 961 PDFs across five doctypes (10 CFR,
Federal Register amendments, SRP, DSRS, RG). Federal Register
amendments do not appear in any Phase-3 evidence chain, so the KG
covers only the four doctypes that participate in the reasoning
paths.

### 5.2 Edges

| Aggregation | NB | MG | LCR | Total |
|-------------|---:|---:|----:|------:|
| Distinct directed typed edges `(src, dst, ref_type)` | **84** | **160** | **148** | **392** |
| Chain-occurrence weight (sum of `rrg:weight`) | **873** | **897** | **403** | **2,173** |

Two aggregations coexist because the KG carries both structural
(distinct edges) and usage (chain-occurrence weight) information. The
distinct-edge count measures the size of the reference graph; the
chain-occurrence weight measures how often each edge is traversed by a
query's evidence chain.

### 5.3 Reuse ratio

Average chain occurrences per distinct edge:

| Type | Distinct | Weight | Reuse ratio |
|------|---------:|-------:|------------:|
| NB | 84 | 873 | **10.4** |
| MG | 160 | 897 | 5.6 |
| LCR | 148 | 403 | 2.7 |

NB edges are reused an order of magnitude more often than LCR edges,
reflecting that the regulatory hierarchy concentrates normative
authority in a small set of legal provisions (primarily 10 CFR
Part 50) that many review and methodology documents cite.

### 5.4 Doctype-level flows (chain-occurrence weight)

Top eight flows `src_doctype -> dst_doctype`:

| Flow | Weight |
|------|-------:|
| SRP -> RG | 588 |
| SRP -> 10CFR | 532 |
| DSRS -> 10CFR | 336 |
| DSRS -> RG | 273 |
| SRP -> SRP | 260 |
| DSRS -> DSRS | 57 |
| RG -> RG | 47 |
| DSRS -> SRP | 43 |

---

## 6. Versioning

- `owl:versionInfo "1.0"` on `<https://regrag.org/ontology>`.
- Instance graph IRI `<https://regrag.org/instances>` declares
  `owl:imports <https://regrag.org/ontology>`.
