import asyncio

from agent.narrative import narrate, template
from agent.orchestrator import Investigation
from tests.fake_mcp import fake_call


def test_template_fallback_without_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    r = asyncio.run(Investigation(fake_call()).run())
    n = asyncio.run(narrate(r))
    assert n["source"] == "template" and "Root cause" in n["text"] and n["error"]


def test_template_mentions_partial():
    r = asyncio.run(Investigation(fake_call(down={"inventory"})).run())
    assert "partial" in template(r)
