"""
mcp_servers/datadog_mcp.py
MCP server exposing Datadog alerts and logs as tools.
Each data source is an independent MCP server — this is the Datadog one.
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mock_data import DATADOG_ALERTS, DATADOG_LOGS

app = Server("datadog-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_datadog_alerts",
            description="Get active Datadog alerts for a given trade ID. Returns severity, status, and message.",
            inputSchema={
                "type": "object",
                "properties": {
                    "trade_id": {"type": "string", "description": "The trade ID to look up alerts for"}
                },
                "required": ["trade_id"],
            },
        ),
        Tool(
            name="get_datadog_logs",
            description="Get Datadog application logs for a given trade ID. Returns timestamped log entries with severity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "trade_id": {"type": "string", "description": "The trade ID to look up logs for"}
                },
                "required": ["trade_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    trade_id = arguments.get("trade_id", "")

    if name == "get_datadog_alerts":
        alerts = DATADOG_ALERTS.get(str(trade_id), [])
        if not alerts:
            result = f"No Datadog alerts found for trade {trade_id}."
        else:
            lines = [f"[{a['severity']}] {a['title']} — {a['message']} (triggered: {a['triggered_at']})" for a in alerts]
            result = f"Datadog alerts for trade {trade_id}:\n" + "\n".join(lines)

    elif name == "get_datadog_logs":
        logs = DATADOG_LOGS.get(str(trade_id), [])
        if not logs:
            result = f"No Datadog logs found for trade {trade_id}."
        else:
            lines = [f"[{l['timestamp']}] [{l['level']}] {l['service']}: {l['message']}" for l in logs]
            result = f"Datadog logs for trade {trade_id}:\n" + "\n".join(lines)

    else:
        result = f"Unknown tool: {name}"

    return [TextContent(type="text", text=result)]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
