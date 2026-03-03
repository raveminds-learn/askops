# AskOps by RaveMinds

> **Ask your infrastructure anything — in plain English, inside Slack.**
> Built with Mistral 7B, LangGraph, MCP, LanceDB, n8n, Langfuse. Zero cloud cost.

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

```
Slack
  ↓
FastAPI :8001
  ↓
LangGraph Agent — Mistral 7B via Ollama
  ├── Supervisor  (classifies intent, extracts trade_id)
  ├── Specialist  (calls all 4 data sources)
  └── Formatter   (plain English answer)
       ↓ MCP Protocol
  ├── datadog_mcp.py  — alerts + logs
  ├── oracle_mcp.py   — trade lifecycle
  ├── kafka_mcp.py    — consumer lag
  └── eks_mcp.py      — pod status
       ↓ historical context
  LanceDB (local vector store)
       ↓ fed by
  n8n  → http://localhost:5678
       ↓ traced by
  Langfuse → http://localhost:3000
```

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
| LangGraph | Multi-agent orchestration |
| MCP | Standardised tool connectivity |
| LanceDB | Local vector store |
| sentence-transformers | Local embeddings |
| n8n | Visual data pipelines |
| Langfuse | AI tracing |
| FastAPI | REST gateway |
| Slack Bolt | Bot interface |
| Docker | Service management |

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
