"""LLM executive summary from the finished report. Facts never depend on this; failure falls back to a template."""
import asyncio
import json
import os
import pathlib

PROMPT = (pathlib.Path(__file__).parent.parent / "prompts" / "report_writer.md").read_text(encoding="utf-8")


def facts(report: dict) -> dict:
    return {
        "status": report["status"],
        "findings": [{k: f[k] for k in ("title", "summary", "status", "confidence_explanation")}
                     for f in report["findings"]],
        "impact": {k: v for k, v in (report["impact"] or {}).items()},
        "actions": [{k: a[k] for k in ("description", "risk_level", "approval_status")} for a in report["actions"]],
        "gaps": report["gaps"],
    }


def template(report: dict) -> str:
    parts = [f"{f['title']} ({f['status']})." for f in report["findings"]]
    if report["gaps"]:
        parts.append(f"This report is partial: {len(report['gaps'])} data source(s) failed.")
    pending = sum(a["approval_status"] == "pending" for a in report["actions"])
    if pending:
        parts.append(f"{pending} recommended action(s) await approval.")
    return " ".join(parts)


async def narrate(report: dict, timeout_s: float = 60) -> dict:
    """Return {text, source: 'llm'|'template', model, error}. Tries LLM_MODEL, then LLM_FALLBACK_MODEL."""
    key = os.getenv("GEMINI_API_KEY")
    models = [m for m in (os.getenv("LLM_MODEL", "gemini-3.8-flash"), os.getenv("LLM_FALLBACK_MODEL")) if m]
    if not key:
        return {"text": template(report), "source": "template", "model": None, "error": "GEMINI_API_KEY not set"}
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=key, http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(attempts=2)))
    errors = []
    for model in models:
        try:
            r = await asyncio.wait_for(client.aio.models.generate_content(
                model=model, contents=PROMPT + json.dumps(facts(report), indent=1),
                config=types.GenerateContentConfig(temperature=0.2)), timeout_s)
            if not r.text:
                raise ValueError("empty response")
            return {"text": r.text.strip(), "source": "llm", "model": model, "error": "; ".join(errors) or None}
        except Exception as e:  # any LLM failure -> next model, finally a labelled template (never a fake AI summary)
            errors.append(f"{model}: {type(e).__name__}: {str(e)[:120]}")
    return {"text": template(report), "source": "template", "model": None, "error": "; ".join(errors)}
