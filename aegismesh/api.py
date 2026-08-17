from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .environment import list_scenarios
from .observability import get_trace
from .orchestrator import AegisMeshOrchestrator
from .report import build_report

app = FastAPI(title="AegisMesh", version="0.1.0")


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    report = build_report()
    s = report["summary"]
    return f"""
    <html><head><title>AegisMesh</title>
    <style>body{{font-family:Inter,Arial;background:#08111f;color:#e5eef8;margin:40px}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}}.card{{background:#111c2e;padding:20px;border:1px solid #26364f;border-radius:14px}}small{{color:#90a4bf}}code{{color:#7dd3fc}}</style></head>
    <body><h1>AegisMesh</h1><p>Multi-Agent AI Security Orchestration · synthetic defensive lab</p>
    <div class="grid">
      <div class="card"><small>WORKFLOW COMPLETION</small><h2>{s['workflow_completion']}</h2></div>
      <div class="card"><small>GROUNDED INVESTIGATIONS</small><h2>{s['grounded_investigations']}</h2></div>
      <div class="card"><small>COUNTERFACTUALS IMPROVED</small><h2>{s['counterfactuals_improved']}</h2></div>
      <div class="card"><small>UNAUTHORIZED TOOLS EXECUTED</small><h2>{s['unauthorized_tools_executed']}</h2></div>
    </div><p><code>Red → Blue → Green → Counterfactual Replay</code></p></body></html>
    """


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": "aegismesh"}


@app.get("/scenarios")
def scenarios() -> list[dict]:
    return [{"id": s.id, "name": s.name, "objective": s.objective} for s in list_scenarios()]


@app.get("/report")
def report() -> dict:
    return build_report()


@app.post("/simulate/{scenario_id}")
def simulate(scenario_id: str) -> dict:
    try:
        return AegisMeshOrchestrator().run(scenario_id).to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/traces/{run_id}")
def traces(run_id: str) -> dict:
    trace = get_trace(run_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="unknown run_id")
    return {"run_id": run_id, "events": trace}
