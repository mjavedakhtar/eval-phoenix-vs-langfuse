"""Shared data-fabric diagnostic agent used by Phoenix and Langfuse runs."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from plant_fabric import get_alarms, get_timeseries, get_work_orders, search_knowledge_graph

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

SYSTEM_PROMPT = """You are a plant diagnostic copilot sitting on an industrial data fabric.

Rules:
- Use tools to query the knowledge graph, time-series, alarms, and work orders.
- Only state facts that a tool returned. Cite asset names, timestamps, codes, and work-order ids.
- If the fabric has no matching asset or data, say so and stop. Do not invent topology, KPIs, or work orders.
- Prefer the smallest tool path that answers the question.
"""


@tool
def search_knowledge_graph_tool(query: str) -> str:
    """Search the plant ontology / knowledge graph for assets, containment, and upstream/downstream relations."""
    return json.dumps(search_knowledge_graph(query), default=str)


@tool
def get_timeseries_tool(asset: str, metric: str) -> str:
    """Fetch recent metric points for an asset. Metrics include scrap_rate and temperature."""
    return json.dumps(get_timeseries(asset, metric), default=str)


@tool
def get_alarms_tool(asset: str) -> str:
    """Fetch recent alarms for an asset id such as Line3, Press12, or OvenA."""
    return json.dumps(get_alarms(asset), default=str)


@tool
def get_work_orders_tool(asset: str) -> str:
    """Fetch maintenance work orders for an asset id."""
    return json.dumps(get_work_orders(asset), default=str)


TOOLS = [
    search_knowledge_graph_tool,
    get_timeseries_tool,
    get_alarms_tool,
    get_work_orders_tool,
]


@lru_cache(maxsize=1)
def get_model():
    """Prefer a local Ollama model so the lab runs with no cloud keys.

    Azure OpenAI / OpenAI are optional upgrades if those keys appear later.
    """
    provider = os.getenv("LLM_PROVIDER", "auto").lower()
    has_azure = bool(os.getenv("AZURE_OPENAI_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    use_ollama = provider == "ollama" or (
        provider == "auto" and not has_azure and not has_openai
    )
    if use_ollama:
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
            temperature=0,
        )

    if has_azure or provider == "azure":
        from langchain_openai import AzureChatOpenAI

        return AzureChatOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
            temperature=0,
        )

    if has_openai or provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
        )

    raise RuntimeError(
        "No model available. Install Ollama (llama3.2:3b) or set AZURE_OPENAI_* / OPENAI_API_KEY."
    )


@lru_cache(maxsize=1)
def get_agent():
    return create_react_agent(get_model(), TOOLS, prompt=SYSTEM_PROMPT)


def run_question(question: str, callbacks: list | None = None) -> dict:
    config = {"callbacks": callbacks} if callbacks else {}
    result = get_agent().invoke(
        {"messages": [HumanMessage(content=question)]},
        config=config,
    )
    messages = result["messages"]
    tool_names = []
    for msg in messages:
        if getattr(msg, "type", None) == "tool" and getattr(msg, "name", None):
            tool_names.append(str(msg.name).removesuffix("_tool"))
    answer = messages[-1].content
    return {
        "question": question,
        "answer": answer,
        "tools_called": tool_names,
        "message_count": len(messages),
    }


def load_golden_set() -> list[dict]:
    path = Path(__file__).parent / "dataset" / "golden.json"
    return json.loads(path.read_text())
