"""Synthetic plant used as a stand-in for a data-fabric API.

No real site, product, or operational data. Assets and numbers are invented
so traces and evals look like a multi-hop industrial agent without depending
on a live system.
"""

from __future__ import annotations

from typing import Any

KNOWLEDGE_GRAPH: dict[str, dict[str, Any]] = {
    "Line3": {
        "type": "ProductionLine",
        "contains": ["Press12", "OvenA"],
        "site": "north",
        "status": "running",
    },
    "Press12": {
        "type": "Equipment",
        "parent": "Line3",
        "upstream": ["WarehouseB"],
        "downstream": ["OvenA"],
        "function": "stamping",
    },
    "OvenA": {
        "type": "Equipment",
        "parent": "Line3",
        "upstream": ["Press12"],
        "function": "curing",
    },
    "WarehouseB": {
        "type": "Storage",
        "downstream": ["Press12"],
        "site": "north",
    },
}

TIMESERIES: dict[tuple[str, str], list[dict[str, Any]]] = {
    ("Line3", "scrap_rate"): [
        {"ts": "2026-09-21T06:00:00Z", "value": 1.2, "unit": "percent"},
        {"ts": "2026-09-21T07:10:00Z", "value": 8.7, "unit": "percent"},
        {"ts": "2026-09-21T08:00:00Z", "value": 7.9, "unit": "percent"},
    ],
    ("Press12", "temperature"): [
        {"ts": "2026-09-21T07:05:00Z", "value": 91.4, "unit": "C"},
        {"ts": "2026-09-21T07:12:00Z", "value": 104.1, "unit": "C"},
    ],
    ("OvenA", "temperature"): [
        {"ts": "2026-09-21T07:00:00Z", "value": 182.0, "unit": "C"},
        {"ts": "2026-09-21T08:00:00Z", "value": 181.6, "unit": "C"},
    ],
}

ALARMS: dict[str, list[dict[str, Any]]] = {
    "Press12": [
        {
            "ts": "2026-09-21T07:08:00Z",
            "code": "OVERHEAT",
            "severity": "high",
            "message": "Die temperature exceeded 100C; overheat interlock fired.",
        }
    ],
    "OvenA": [
        {
            "ts": "2026-09-20T22:14:00Z",
            "code": "TC_DRIFT",
            "severity": "warning",
            "message": "Thermocouple drift detected on zone 2.",
        }
    ],
    "Line3": [],
}

WORK_ORDERS: dict[str, list[dict[str, Any]]] = {
    "OvenA": [
        {
            "id": "WO-4419",
            "opened": "2026-09-18",
            "status": "in_progress",
            "summary": "Replace zone 2 thermocouple after drift alarm.",
        }
    ],
    "Press12": [
        {
            "id": "WO-4380",
            "opened": "2026-08-02",
            "status": "closed",
            "summary": "Quarterly die inspection.",
        }
    ],
    "Line3": [],
}


def search_knowledge_graph(query: str) -> dict[str, Any]:
    """Keyword lookup over the simulated ontology / knowledge graph."""
    q = query.lower()
    hits = {
        name: node
        for name, node in KNOWLEDGE_GRAPH.items()
        if name.lower() in q
        or any(str(v).lower().find(q) >= 0 for v in node.values())
        or q.strip() in name.lower()
    }
    if not hits:
        tokens = {t for t in q.replace("-", " ").split() if len(t) > 2}
        hits = {
            name: node
            for name, node in KNOWLEDGE_GRAPH.items()
            if name.lower() in tokens
            or any(str(v).lower() in tokens for v in _flatten(node))
        }
    return {"query": query, "hits": hits, "hit_count": len(hits)}


def get_timeseries(asset: str, metric: str) -> dict[str, Any]:
    series = TIMESERIES.get((asset, metric))
    if series is None:
        return {
            "asset": asset,
            "metric": metric,
            "points": [],
            "error": "No series in fabric for this asset/metric.",
        }
    return {"asset": asset, "metric": metric, "points": series}


def get_alarms(asset: str) -> dict[str, Any]:
    if asset not in ALARMS and asset not in KNOWLEDGE_GRAPH:
        return {"asset": asset, "alarms": [], "error": "Asset not in fabric."}
    return {"asset": asset, "alarms": ALARMS.get(asset, [])}


def get_work_orders(asset: str) -> dict[str, Any]:
    if asset not in WORK_ORDERS and asset not in KNOWLEDGE_GRAPH:
        return {"asset": asset, "work_orders": [], "error": "Asset not in fabric."}
    return {"asset": asset, "work_orders": WORK_ORDERS.get(asset, [])}


def _flatten(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v).lower() for v in value]
    return [str(value).lower()]
