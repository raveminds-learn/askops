"""
mcp_servers/kafka_mcp.py
MCP server exposing Kafka consumer lag data as tools.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mock_data import KAFKA_LAG

app = Server("kafka-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_kafka_lag",
            description="Get Kafka consumer lag for topics related to a trade. Returns lag per topic, status (HEALTHY/WARN/CRITICAL), and historical patterns.",
            inputSchema={
                "type": "object",
                "properties": {
                    "trade_id": {"type": "string", "description": "The trade ID to check Kafka lag for"}
                },
                "required": ["trade_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    trade_id = str(arguments.get("trade_id", ""))

    if name == "get_kafka_lag":
        data = KAFKA_LAG.get(trade_id)
        if not data:
            return [TextContent(type="text", text=f"No Kafka data found for trade {trade_id}.")]

        lines = [f"Kafka snapshot at {data['snapshot_time']}:", ""]
        for topic in data.get("topics", []):
            lines.append(f"  [{topic['status']}] {topic['topic']}")
            lines.append(f"    Consumer group : {topic['consumer_group']}")
            lines.append(f"    Total lag      : {topic['total_lag']:,} messages")
            lines.append(f"    Note           : {topic['note']}")
            lines.append("")

        if data.get("pattern"):
            lines.append(f"Pattern: {data['pattern']}")

        return [TextContent(type="text", text="\n".join(lines))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
