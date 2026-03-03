"""
agent/graph.py — AskOps by RaveMinds
========================================
Optimized for <60s: 1 LLM call, regex trade extraction.
Generates business, manager, technical in one pass; full = concat.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_community.llms import Ollama
from langgraph.graph import StateGraph, END

from mock_data import get_trade_context
from storage.lancedb_store import search as lancedb_search

llm = Ollama(model="mistral", temperature=0, num_predict=512)


# ── State ──────────────────────────────────────────────────────────
from typing import TypedDict

class AgentState(TypedDict):
    question: str
    trade_id: str
    raw_data: dict
    historical: str
    view_business: str
    view_manager: str
    view_technical: str
    view_full: str


def _extract_trade_id(question: str) -> str:
    """Extract 5-digit trade ID with regex — no LLM needed."""
    known = {"12345", "22222", "33333", "44444", "55555"}
    matches = re.findall(r"\b(\d{5})\b", question)
    for m in matches:
        if m in known:
            return m
    return matches[0] if matches else ""


def _get_historical(query: str, trade_id: str) -> str:
    results = lancedb_search(query, trade_id=trade_id, top_k=3)
    if not results:
        return "No historical patterns found."
    lines = [f"[{r['timestamp']}] {r['service']}: {r['content']}" for r in results]
    return "Historical context:\n" + "\n".join(lines)


def data_collector_node(state: AgentState) -> dict:
    trade_id = state.get("trade_id", "")
    if not trade_id:
        return {"raw_data": {}, "historical": "No trade ID found."}

    raw_data = get_trade_context(trade_id)
    historical = _get_historical(state["question"], trade_id)
    return {"raw_data": raw_data, "historical": historical}


def _format_context(state: AgentState) -> str:
    """Format raw_data + historical for the combined prompt."""
    data = state.get("raw_data", {})
    oracle = data.get("oracle", {})
    mgr = data.get("manager_summary", {})
    apm = data.get("datadog_apm", {})
    logs = data.get("datadog_logs", [])[:5]
    kafka = data.get("kafka", {})
    eks = data.get("eks", {})
    app_events = data.get("app_events", [])

    events = "\n".join([f"- {e['business_context']}" for e in app_events]) or "No events."
    logs_txt = "\n".join([f"[{l['level']}] {l['service']}: {l['message']}" for l in logs])
    spans = ""
    for s in apm.get("spans", []):
        err = s.get("error", s.get("note", ""))
        spans += f"  [{s.get('status')}] {s['service']}.{s['operation']} — {s['duration_ms']}ms"
        if err:
            spans += f"\n    └─ {err}\n"
        else:
            spans += "\n"
    topics = "\n".join([f"  [{t.get('status')}] {t.get('topic')} lag:{t.get('total_lag',0):,}" for t in kafka.get("topics", [])]) or "  No Kafka issues"
    pods = ""
    for p in eks.get("pods", []):
        icon = "🔴" if p.get("status") == "CrashLoopBackOff" else "🟢"
        pods += f"  {icon} {p['name']} — {p.get('status')} restarts:{p.get('restarts',0)}\n"

    return f"""ORACLE: {oracle.get('trade_id')} | {oracle.get('status')} | {oracle.get('business_impact')} | exposure: {oracle.get('financial_exposure')}
MANAGER: trades_affected={mgr.get('trades_affected')} sla_breach={mgr.get('sla_breach')} pattern={mgr.get('pattern')} action={mgr.get('action_required')}
APM: {apm.get('app_root_cause')} | layer={apm.get('layer')}
Spans: {spans}
Logs: {logs_txt}
Kafka: {topics}
EKS: {pods}
{state.get('historical', '')}
Events: {events}"""


def combined_views_node(state: AgentState) -> dict:
    """One LLM call for business + manager + technical."""
    ctx = _format_context(state)
    prompt = f"""You are AskOps. User asked: "{state['question']}"

Data:
{ctx}

Reply EXACTLY in this format (no extra text). Do not use emojis or status icons.

BUSINESS:
<2-4 lines, plain English, state the status in words (e.g. FAILED, PENDING, SETTLED)>

MANAGER:
<bullet points: status, SLA, exposure, action needed>

TECHNICAL:
<bullet points: root cause, service, infra, fix>"""

    out = llm.invoke(prompt)
    business, manager, technical = "", "", ""
    section = None
    buf = []
    for line in out.split("\n"):
        if line.strip().startswith("BUSINESS:"):
            section = "business"
            buf = [line.replace("BUSINESS:", "").strip()]
        elif line.strip().startswith("MANAGER:"):
            if section == "business":
                business = "\n".join(buf).strip()
            section = "manager"
            buf = [line.replace("MANAGER:", "").strip()]
        elif line.strip().startswith("TECHNICAL:"):
            if section == "manager":
                manager = "\n".join(buf).strip()
            section = "technical"
            buf = [line.replace("TECHNICAL:", "").strip()]
        elif section:
            buf.append(line.strip())
    if section == "technical":
        technical = "\n".join(buf).strip()

    # Strip status emojis (red/yellow/green/white circles)
    def strip_icons(t: str) -> str:
        return re.sub(r"[🔴🟡🟢⚪🟠]\s*", "", t).strip() if t else t

    business = strip_icons(business)
    manager = strip_icons(manager)
    technical = strip_icons(technical)

    full = f"## Summary\n{business}\n\n## Manager\n{manager}\n\n## Technical\n{technical}"
    return {"view_business": business, "view_manager": manager, "view_technical": technical, "view_full": full}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("data_collector", data_collector_node)
    graph.add_node("combined_views", combined_views_node)
    graph.set_entry_point("data_collector")
    graph.add_edge("data_collector", "combined_views")
    graph.add_edge("combined_views", END)
    return graph.compile()


_graph = None


def ask(question: str) -> dict:
    global _graph
    if _graph is None:
        _graph = build_graph()

    trade_id = _extract_trade_id(question)
    result = _graph.invoke({
        "question": question, "trade_id": trade_id,
        "raw_data": {}, "historical": "",
        "view_business": "", "view_manager": "", "view_technical": "", "view_full": "",
    })
    return {
        "business": result["view_business"],
        "manager": result["view_manager"],
        "technical": result["view_technical"],
        "full": result["view_full"],
        "trade_id": result["trade_id"],
    }


if __name__ == "__main__":
    r = ask("What happened to trade 12345?")
    print("BUSINESS:", r["business"])
    print("MANAGER:", r["manager"])
    print("TECHNICAL:", r["technical"])
