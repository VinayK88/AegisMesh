from __future__ import annotations


def build_evidence_graph(red_payload: dict) -> dict:
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    for item in red_payload.get("evidence", []):
        source = item["source"]
        target = item["target"]
        nodes.setdefault(source, {"id": source, "kind": "entity"})
        nodes.setdefault(target, {"id": target, "kind": "entity"})
        nodes[item["id"]] = {"id": item["id"], "kind": "evidence", "summary": item["summary"]}
        edges.append({"source": source, "target": item["id"], "relation": "supported_by"})
        edges.append({"source": item["id"], "target": target, "relation": "observes"})

    return {"nodes": sorted(nodes.values(), key=lambda n: n["id"]), "edges": edges}
