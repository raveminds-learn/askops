"""
mcp_servers/oracle_mcp.py
MCP server exposing Oracle trade lifecycle data as tools.
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mock_data import ORACLE_TRADES

app = Server("oracle-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_trade_lifecycle",
            description="Get the full lifecycle of a trade from Oracle. Returns current status, all state transitions, errors, and SLA breach info.",
            inputSchema={
                "type": "object",
                "properties": {
                    "trade_id": {"type": "string", "description": "The trade ID to look up"}
                },
                "required": ["trade_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    trade_id = str(arguments.get("trade_id", ""))

    if name == "get_trade_lifecycle":
        trade = ORACLE_TRADES.get(trade_id)
        if not trade:
            return [TextContent(type="text", text=f"Trade {trade_id} not found in Oracle.")]

        lines = [
            f"Trade {trade_id} | {trade['instrument']} {trade['direction']} {trade['quantity']} @ {trade['price']}",
            f"Trader: {trade['trader']}",
            f"Status: {trade['status']} | SLA Breach: {trade['sla_breach']}",
            "",
            "Lifecycle:",
        ]
        for step in trade["lifecycle"]:
            lines.append(f"  [{step['timestamp']}] {step['state']} — {step['note']}")

        if trade.get("error"):
            lines.append(f"\nError: {trade['error']}")
        if trade.get("duplicate_of"):
            lines.append(f"Duplicate of trade: {trade['duplicate_of']}")
        if trade.get("notional_value"):
            lines.append(f"Notional: ${trade['notional_value']:,} | Limit: ${trade['trader_limit']:,}")
        if trade.get("settlement_duration_seconds"):
            lines.append(f"Settlement time: {trade['settlement_duration_seconds']}s | SLA: {trade['sla_threshold_seconds']}s")

        return [TextContent(type="text", text="\n".join(lines))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
