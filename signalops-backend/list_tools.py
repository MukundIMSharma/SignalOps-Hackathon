import asyncio
import sys

from mcp_clients.servers import SERVERS, connect


async def main():
    for name in SERVERS:
        async with connect(name) as s:
            tools = (await s.list_tools()).tools
            print(f"[{name}] {len(tools)} tools")
            for t in tools:
                print(f"  {t.name}: {(t.description or '')[:90]}")


asyncio.run(main()) if __name__ == "__main__" else None
