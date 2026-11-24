"""Synapse-generated MCP servers (stdio via npx). Server IDs come from `synapse build` output."""
import os
import shutil
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

SERVERS = {
    "orders": {"server_id": "6ab65632-0790-4e06-8b0e-77bb3d448920",
               "base_url": os.getenv("ORDERS_API_URL", "http://localhost:8001")},
    "inventory": {"server_id": "bf451b7a-95c9-4658-b2a6-91708fb7ef84",
                  "base_url": os.getenv("INVENTORY_API_URL", "http://localhost:8002")},
}


def params(name: str) -> StdioServerParameters:
    s = SERVERS[name]
    env = {**os.environ, "SYNAPSE_SERVER_ID": s["server_id"], "ENDPOINT_BASE_URL": s["base_url"]}
    return StdioServerParameters(command=shutil.which("npx") or "npx",
                                 args=["-y", "@2ndbrainlabs-ai/synapse-mcp"], env=env)


@asynccontextmanager
async def connect(name: str):
    async with stdio_client(params(name)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


@asynccontextmanager
async def open_caller():
    """Keep one MCP session per server open; yield call(server, tool, args) -> parsed JSON (ToolError on failure)."""
    import json
    from contextlib import AsyncExitStack

    from agent.orchestrator import ToolError

    async with AsyncExitStack() as stack:
        sessions = {}
        for name in SERVERS:
            try:
                sessions[name] = await stack.enter_async_context(connect(name))
            except Exception as e:  # a server that won't start becomes a per-call ToolError -> partial report
                sessions[name] = e

        async def call(server: str, tool: str, args: dict):
            s = sessions[server]
            if isinstance(s, Exception):
                raise ToolError(f"{server} MCP server not connected: {s}")
            r = await s.call_tool(tool, args)
            body = json.loads(r.content[0].text) if r.content else None
            if r.is_error:
                raise ToolError(f"{tool}: {body}")
            return body

        yield call
