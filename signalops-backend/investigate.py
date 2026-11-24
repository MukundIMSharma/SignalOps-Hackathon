"""Terminal investigation over the live Synapse MCP servers. Usage: python investigate.py [--json]"""
import asyncio
import json
import sys

from agent.narrative import narrate
from agent.orchestrator import Investigation
from mcp_clients.servers import open_caller


async def main():
    async with open_caller() as call:
        report = await Investigation(call, on_event=lambda e: e["type"] == "tool_call" and print(
            f"  [{e['server']:9}] {e['tool']:26} {'ok ' if e['ok'] else 'ERR'} {e['ms']:5}ms  {e['summary']}",
            file=sys.stderr)).run()
    report["narrative"] = await narrate(report)
    if "--json" in sys.argv:
        print(json.dumps(report, indent=1)); return
    n = report["narrative"]
    print(f"\nSUMMARY ({n['source']}{', ' + n['error'] if n['error'] else ''}):\n  {n['text']}")
    print(f"\nSTATUS: {report['status']}   as_of {report['as_of']}")
    for f in report["findings"]:
        print(f"\n[{f['status'].upper()}] {f['title']}\n  {f['summary']}\n  evidence: {', '.join(f['evidence_ids'])}")
    if report["impact"]:
        print("\nIMPACT")
        for k, v in report["impact"].items():
            print(f"  {k:28} {v['value']}")
        print("\nTOP 5 PRIORITIES")
        for p in report["priorities"][:5]:
            print(f"  #{p['rank']} {p['order_id']} {p['customer_name']:14} score {p['score']:3}  {'; '.join(p['reasons'])}")
    print("\nACTIONS")
    for a in report["actions"]:
        print(f"  {a['action_id']} [{a['risk_level']}] {a['description']}  -> {a['approval_status']}")
    if report["gaps"]:
        print("\nGAPS:", *report["gaps"], sep="\n  ")


asyncio.run(main())
