"""Phoenix OTLP HTTP traces URL. Shared by the agent lab and the MCP lab."""

from __future__ import annotations

import os


def traces_endpoint() -> str:
    base = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006").rstrip("/")
    if base.endswith("/v1/traces"):
        return base
    return f"{base}/v1/traces"
