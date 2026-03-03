"""
mcp_servers/eks_mcp.py
MCP server exposing EKS pod status as tools.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mock_data import EKS_PODS

app = Server("eks-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_eks_pod_status",
            description="Get EKS pod health for services related to a trade. Returns pod status, restart counts, CPU/memory usage, and HPA status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "trade_id": {"type": "string", "description": "The trade ID to check pod status for"}
                },
                "required": ["trade_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    trade_id = str(arguments.get("trade_id", ""))

    if name == "get_eks_pod_status":
        data = EKS_PODS.get(trade_id)
        if not data:
            return [TextContent(type="text", text=f"No EKS data found for trade {trade_id}.")]

        lines = [
            f"EKS snapshot at {data['snapshot_time']}",
            f"Namespace: {data['namespace']}",
            "",
            "Pods:",
        ]
        for pod in data.get("pods", []):
            status_icon = "🔴" if pod["status"] == "CrashLoopBackOff" else "🟢"
            lines.append(f"  {status_icon} {pod['name']}")
            lines.append(f"     Status   : {pod['status']} | Restarts: {pod.get('restarts', 0)}")
            lines.append(f"     CPU      : {pod.get('cpu', 'N/A')} | Memory: {pod.get('memory', 'N/A')}")
            if pod.get("reason"):
                lines.append(f"     Reason   : {pod['reason']}")
            if pod.get("last_restart"):
                lines.append(f"     Last restart: {pod['last_restart']}")
            lines.append("")

        hpa = data.get("hpa")
        if hpa:
            lines.append(f"HPA: {hpa.get('current_replicas')} running / {hpa.get('desired_replicas')} desired")
            lines.append(f"     {hpa.get('note', '')}")

        return [TextContent(type="text", text="\n".join(lines))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
