# AskOps by RaveMinds

> **Ask your infrastructure anything — in plain English, inside Slack.**
> Built with Mistral 7B, LangGraph, LanceDB. Optional: MCP servers, n8n, Langfuse (in repo/Docker; not in the live flow). Zero cloud cost.

---

## The Problem

Every day, business teams ping engineers:
*"What happened to trade 12345?"*

The engineer drops everything, opens 4 dashboards, queries the DB, reads logs, replies 10 minutes later.

Multiply that by 20 engineers, 10 times a day. Thousands of hours of lost engineering time every year.

## The Solution

AskOps sits in Slack and answers in plain English — in under 5 seconds.

```
You:    What happened to trade 12345?

AskOps: 🔴 Trade 12345 — FAILED

        • 09:47 AM — Received and validated ✓
        • 10:30 AM — Kafka lag spiked to 45,000 messages
        • 10:33 AM — Settlement service timed out
        • 10:34 AM — EKS pod restarted twice (OOMKilled)
        • 10:35 AM — Trade moved to FAILED state

        Root cause: Settlement pod instability + Kafka backlog.
        Same pattern seen last Tuesday.
        Trade has NOT been reprocessed.
```

---

## One-Click Setup

```bat
setup.bat
```

Automatically starts Docker Desktop, Ollama, pulls Mistral, installs everything.

---

## Prerequisites

| Tool | Install |
|---|---|
| Python 3.11 | https://python.org |
| Docker Desktop | https://docker.com |
| Ollama | https://ollama.ai |
| Cursor IDE | https://cursor.sh |
| ngrok (free) | https://ngrok.com |

---

## Running the Demo

**Single command** (API + Slack bot in separate windows):

```bat
start.bat
```

To stop both: `stop.bat`

---

Or run manually in separate terminals:

```bat
start_api.bat          # Terminal 1 — FastAPI on :8001
start_bot.bat          # Terminal 2 — Slack bot
python test_demo.py    # Terminal 3 — test without Slack
```

---

## Demo Trade Scenarios

| Trade | Scenario | Status |
|---|---|---|
| 12345 | Settlement timeout + pod OOMKilled + Kafka spike | FAILED |
| 22222 | Duplicate of trade 22198 within 5-min window | REJECTED |
| 33333 | Full outage — all pods CrashLoopBackOff | PENDING |
| 44444 | Settled in 8m 34s vs 2min SLA | SETTLED |
| 55555 | Notional $8.75M exceeds trader limit $5M | REJECTED |

---

## Architecture

**Actual flow (what runs when you ask in Slack):**

```
Slack
  ↓
Slack Bolt bot  →  FastAPI :8001
  ↓
LangGraph agent (agent/graph.py)
  ├── Regex trade_id extraction (no LLM)
  ├── data_collector node
  │     ├── mock_data.get_trade_context(trade_id)  → Oracle, Datadog, Kafka, EKS, manager summary
  │     └── LanceDB semantic search (historical context)
  └── combined_views node  →  one Ollama (Mistral) call  →  business + manager + technical
  ↓
Answer back to Slack
```

**Optional / not in the live flow:**
- **MCP servers** (mcp_servers/*.py) — present in repo; would need an MCP client in the agent to be used.
- **LanceDB** is populated by `ingestion/ingest.py` (mock logs); **n8n** and **Langfuse** are in Docker for pipelines and tracing if you wire them up.

---

## Services

| Service | URL |
|---|---|
| API | http://localhost:8001 |
| API Docs | http://localhost:8001/docs |
| n8n Pipelines | http://localhost:5678 |
| Langfuse Traces | http://localhost:3000 |

---

## Stack (All Free)

| Tool | Role |
|---|---|
| Mistral 7B + Ollama | Local LLM |
| LangGraph | Agent graph (data_collector → combined_views) |
| mock_data + LanceDB | Trade context + historical search (demo) |
| FastAPI | REST gateway |
| Slack Bolt | Bot interface |
| Docker | n8n, Langfuse, Postgres, Redis (optional) |

*MCP servers and n8n are in the repo/Docker but not called by the current flow.*

**Total cost: $0**

---

## Slack App Setup

1. Go to https://api.slack.com/apps
2. **Create New App** → From Scratch → name it `AskOps`
3. **OAuth & Permissions** → Bot Token Scopes:
   - `app_mentions:read`
   - `chat:write`
   - `im:history`
   - `reactions:write`
4. **Install to Workspace** → copy **Bot User OAuth Token** → `.env` as `SLACK_BOT_TOKEN`
5. **Socket Mode** → Enable → generate App-Level Token → `.env` as `SLACK_APP_TOKEN`
6. **Event Subscriptions** → Enable → subscribe to: `app_mention`, `message.im`
7. Reinstall app to workspace

---

*AskOps by RaveMinds — Build in public*
*Follow the journey on LinkedIn*
