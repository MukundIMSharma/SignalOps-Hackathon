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
