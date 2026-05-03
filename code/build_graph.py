#!/usr/bin/env python3
"""
build_graph.py
--------------
Build the NuReg-XDoc document-level reference Knowledge Graph (KG)
from nureg-xdoc-queries.json.

Outputs (default --outdir=graph):
  ontology.ttl          W3C OWL schema only (no instance data)
  instances.ttl         RDF instance data that owl:imports the ontology
  nodes.csv             flat node dump (doc_id, doc_type, degree, query_count)
  edges.csv             flat directed typed edge dump with weights and example qids
  cooccurrence_edges.csv undirected co-occurrence dump (for analysis; not part of KG)

Edge induction (directed, typed):
  For every evidence_chain in a query entry, for every fact F_j with
  hop > 0 and reference_type != None:
    src = nearest preceding fact F_i with hop = F_j.hop - 1
          (fallback: the chain's hop=0 fact)
    dst = F_j.doc_id
    pred = reference_type
  Self-loops are dropped. Edge identity is (src, dst, pred); multiple chains
  touching the same edge collapse onto one edge whose weight records the
  chain-occurrence count.
"""

from __future__ import annotations
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

# Canonical value set - the KG supports exactly these four doctypes.
ALLOWED_DOCTYPES = ("10CFR", "SRP", "DSRS", "RG")

REF_TYPES = (
    "normative_basis",
    "methodology_guidance",
    "lateral_cross_reference",
)

REF_TYPE_TO_PRED = {
    "normative_basis": "rrg:normativeBasis",
    "methodology_guidance": "rrg:methodologyGuidance",
    "lateral_cross_reference": "rrg:lateralCrossReference",
}

ONTOLOGY_IRI = "https://regrag.org/ontology"
INSTANCE_IRI = "https://regrag.org/instances"

ONTOLOGY_TTL = """@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix rrg:  <https://regrag.org/ontology#> .

# -----------------------------------------------------------------------------
# Ontology header
# -----------------------------------------------------------------------------
<https://regrag.org/ontology> a owl:Ontology ;
    rdfs:label "NuReg-XDoc Document-Level Reference Knowledge Graph Ontology" ;
    owl:versionInfo "1.0" ;
    rdfs:comment "Minimal OWL schema for a document-level regulatory reference KG. Nodes are regulatory documents; edges are typed inter-document references licensed by explicit clauses in the source documents." .

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------
rrg:RegulatoryDocument a owl:Class ;
    rdfs:label "Regulatory Document" ;
    rdfs:comment "A single regulatory document participating in the KG." .

# -----------------------------------------------------------------------------
# Datatype properties on RegulatoryDocument
# -----------------------------------------------------------------------------
rrg:docType a owl:DatatypeProperty , owl:FunctionalProperty ;
    rdfs:domain rrg:RegulatoryDocument ;
    rdfs:range [
        a rdfs:Datatype ;
        owl:onDatatype xsd:string ;
        owl:oneOf ( "10CFR" "SRP" "DSRS" "RG" )
    ] ;
    rdfs:label "document type" ;
    rdfs:comment "Enumerated doctype: one of {10CFR, SRP, DSRS, RG}." .

rrg:queryCount a owl:DatatypeProperty ;
    rdfs:domain rrg:RegulatoryDocument ;
    rdfs:range xsd:nonNegativeInteger ;
    rdfs:label "query count" ;
    rdfs:comment "Number of benchmark queries whose evidence chain touches this document." .

# -----------------------------------------------------------------------------
# Object properties: typed inter-document references
# rrg:references is the superproperty; the three typed sub-properties are
# licensed by distinct clause patterns in the source documents.
# -----------------------------------------------------------------------------
rrg:references a owl:ObjectProperty ;
    rdfs:domain rrg:RegulatoryDocument ;
    rdfs:range rrg:RegulatoryDocument ;
    rdfs:label "references" ;
    rdfs:comment "Asserts a typed inter-document reference between regulatory documents." .

rrg:normativeBasis a owl:ObjectProperty ;
    rdfs:subPropertyOf rrg:references ;
    rdfs:label "normative basis" ;
    rdfs:comment "Licensed by compliance clauses (e.g., 'shall comply with ...'). Review or methodology document to legal authority." .

rrg:methodologyGuidance a owl:ObjectProperty ;
    rdfs:subPropertyOf rrg:references ;
    rdfs:label "methodology guidance" ;
    rdfs:comment "Licensed by acceptable-method clauses (e.g., 'an acceptable method is ...'). Review document to methodology document." .

rrg:lateralCrossReference a owl:ObjectProperty ;
    rdfs:subPropertyOf rrg:references ;
    rdfs:label "lateral cross-reference" ;
    rdfs:comment "Licensed by 'see also' clauses. Between sections of the same role." .

# -----------------------------------------------------------------------------
# Edge weight (on reified statements)
# -----------------------------------------------------------------------------
rrg:weight a owl:DatatypeProperty ;
    rdfs:domain rdf:Statement ;
    rdfs:range xsd:positiveInteger ;
    rdfs:label "edge weight" ;
    rdfs:comment "Number of evidence chains that traverse the reified (src, pred, dst) edge." .
"""


def slugify(doc_id: str) -> str:
    """Turn a doc_id like '10 CFR Part 50' into a URI-safe suffix."""
    return (
        doc_id.replace(" ", "_")
        .replace(".", "-")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
        .replace(",", "")
    )


def extract_graph(dataset: dict):
    entries = dataset["data"]

    nodes: dict[str, str] = {}  # doc_id -> doc_type
    query_count: Counter = Counter()
    directed_edges: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    cooc_edges: Counter = Counter()

    for e in entries:
        qid = e["query_id"]
        facts = e["evidence_chain"]
        if not facts:
            continue

        # Register nodes with doctype validation.
        for f in facts:
            d = f["doc_id"]
            dt = f["doc_type"]
            if dt not in ALLOWED_DOCTYPES:
                raise ValueError(
                    f"Doctype '{dt}' for doc '{d}' in query {qid} "
                    f"is outside the KG-permitted set {ALLOWED_DOCTYPES}"
                )
            nodes.setdefault(d, dt)
            query_count[d] += 1

        # Co-occurrence (undirected) edges
        doc_ids = sorted({f["doc_id"] for f in facts})
        for i in range(len(doc_ids)):
            for j in range(i + 1, len(doc_ids)):
                cooc_edges[(doc_ids[i], doc_ids[j])] += 1

        # Directed typed edges via predecessor rule
        for j, fj in enumerate(facts):
            rt = fj.get("reference_type")
            hop = fj.get("hop", 0)
            if hop is None or hop <= 0 or rt not in REF_TYPES:
                continue
            src = None
            for i in range(j - 1, -1, -1):
                if facts[i].get("hop") == hop - 1:
                    src = facts[i]["doc_id"]
                    break
            if src is None:
                src = facts[0]["doc_id"]
            dst = fj["doc_id"]
            if src == dst:
                continue
            directed_edges[(src, dst, rt)].append(qid)

    return nodes, query_count, directed_edges, cooc_edges


def write_nodes(path: Path, nodes: dict[str, str], query_count: Counter,
                directed_edges: dict) -> None:
    in_deg: Counter = Counter()
    out_deg: Counter = Counter()
    for (s, d, _rt), qs in directed_edges.items():
        w = len(qs)
        out_deg[s] += w
        in_deg[d] += w

    rows = []
    for doc_id, doc_type in sorted(nodes.items()):
        rows.append({
            "doc_id": doc_id,
            "doc_type": doc_type,
            "query_count": query_count[doc_id],
            "out_degree_weighted": out_deg[doc_id],
            "in_degree_weighted": in_deg[doc_id],
        })

    with path.open("w", newline="", encoding="utf-8") as fp:
        w = csv.DictWriter(fp, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def write_directed_edges(path: Path, directed_edges: dict) -> None:
    rows = []
    for (s, d, rt), qids in sorted(directed_edges.items()):
        rows.append({
            "src": s,
            "dst": d,
            "reference_type": rt,
            "weight": len(qids),
            "example_query_ids": ";".join(qids[:3]),
        })
    with path.open("w", newline="", encoding="utf-8") as fp:
        w = csv.DictWriter(
            fp,
            fieldnames=["src", "dst", "reference_type", "weight", "example_query_ids"],
        )
        w.writeheader()
        w.writerows(rows)


def write_cooc_edges(path: Path, cooc_edges: Counter) -> None:
    rows = [
        {"src": s, "dst": d, "weight": w}
        for (s, d), w in sorted(cooc_edges.items(), key=lambda x: (-x[1], x[0]))
    ]
    with path.open("w", newline="", encoding="utf-8") as fp:
        wr = csv.DictWriter(fp, fieldnames=["src", "dst", "weight"])
        wr.writeheader()
        wr.writerows(rows)


def write_ontology(path: Path) -> None:
    path.write_text(ONTOLOGY_TTL, encoding="utf-8")


def write_instances(path: Path, nodes: dict[str, str], query_count: Counter,
                    directed_edges: dict) -> None:
    lines = [
        "@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix owl:  <http://www.w3.org/2002/07/owl#> .",
        "@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .",
        "@prefix rrg:  <https://regrag.org/ontology#> .",
        "@prefix doc:  <https://regrag.org/doc/> .",
        "",
        "# Instance graph - imports the NuReg-XDoc ontology.",
        f"<{INSTANCE_IRI}> a owl:Ontology ;",
        f"    owl:imports <{ONTOLOGY_IRI}> ;",
        '    rdfs:label "NuReg-XDoc KG instance data (v1.0.0)" .',
        "",
        "# -----------------------------------------------------------------------------",
        f"# Regulatory document nodes ({len(nodes)} instances)",
        "# -----------------------------------------------------------------------------",
    ]
    for doc_id, doc_type in sorted(nodes.items()):
        uri = f"doc:{slugify(doc_id)}"
        lines.append(f"{uri} a rrg:RegulatoryDocument ;")
        lines.append(f'    rdfs:label "{doc_id}" ;')
        lines.append(f'    rrg:docType "{doc_type}" ;')
        lines.append(f"    rrg:queryCount {query_count[doc_id]} .")
        lines.append("")
    lines.append("# -----------------------------------------------------------------------------")
    lines.append(f"# Typed inter-document references ({len(directed_edges)} distinct edges)")
    lines.append("# Each edge is asserted as a direct triple and reified to carry a weight.")
    lines.append("# -----------------------------------------------------------------------------")
    for i, ((s, d, rt), qids) in enumerate(sorted(directed_edges.items())):
        su = f"doc:{slugify(s)}"
        du = f"doc:{slugify(d)}"
        pred = REF_TYPE_TO_PRED[rt]
        w = len(qids)
        lines.append(f"{su} {pred} {du} .")
        lines.append(
            f"_:e{i} a rdf:Statement ; "
            f"rdf:subject {su} ; "
            f"rdf:predicate {pred} ; "
            f"rdf:object {du} ; "
            f"rrg:weight {w} ."
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(nodes, query_count, directed_edges, cooc_edges):
    print(f"Nodes (unique regulatory documents): {len(nodes)}")
    doc_type_counts = Counter(nodes.values())
    print(f"  by doc_type: {dict(doc_type_counts)}")

    print(f"\nUndirected co-occurrence edges: {len(cooc_edges)}")
    print(f"  total weight: {sum(cooc_edges.values())}")

    print(f"\nDirected typed edges (distinct): {len(directed_edges)}")
    total_w = sum(len(v) for v in directed_edges.values())
    print(f"  total chain-occurrence weight: {total_w}")
    by_type_distinct = Counter()
    by_type_weight = Counter()
    for (_, _, rt), qs in directed_edges.items():
        by_type_distinct[rt] += 1
        by_type_weight[rt] += len(qs)
    print("  distinct edges by reference type:")
    for rt in REF_TYPES:
        print(f"    {rt}: {by_type_distinct[rt]}")
    print("  chain-occurrence weight by reference type:")
    for rt in REF_TYPES:
        print(f"    {rt}: {by_type_weight[rt]}")

    print("\nDirected flows by (src_doc_type -> dst_doc_type) [weighted]:")
    flow = Counter()
    for (s, d, _rt), qs in directed_edges.items():
        flow[(nodes[s], nodes[d])] += len(qs)
    for (st, dt), w in sorted(flow.items(), key=lambda x: -x[1]):
        print(f"  {st} -> {dt}: {w}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--input",
        default="data/nureg-xdoc-queries.json",
        help="Path to the QA dataset JSON",
    )
    p.add_argument(
        "--outdir",
        default="graph",
        help="Output directory for graph artifacts",
    )
    p.add_argument(
        "--ontology-out",
        default=None,
        help="Override output path for ontology.ttl (default: <outdir>/ontology.ttl)",
    )
    p.add_argument(
        "--instances-out",
        default=None,
        help="Override output path for instances.ttl (default: <outdir>/instances.ttl)",
    )
    args = p.parse_args()

    with open(args.input, encoding="utf-8") as fp:
        dataset = json.load(fp)

    nodes, query_count, directed_edges, cooc_edges = extract_graph(dataset)

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    ontology_path = Path(args.ontology_out) if args.ontology_out else out / "ontology.ttl"
    instances_path = Path(args.instances_out) if args.instances_out else out / "instances.ttl"

    write_nodes(out / "nodes.csv", nodes, query_count, directed_edges)
    write_directed_edges(out / "edges.csv", directed_edges)
    write_cooc_edges(out / "cooccurrence_edges.csv", cooc_edges)
    write_ontology(ontology_path)
    write_instances(instances_path, nodes, query_count, directed_edges)

    print_summary(nodes, query_count, directed_edges, cooc_edges)
    print(f"\nWrote ontology to:  {ontology_path.resolve()}")
    print(f"Wrote instances to: {instances_path.resolve()}")
    print(f"Wrote CSVs to:      {out.resolve()}")


if __name__ == "__main__":
    main()
