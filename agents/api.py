"""FastAPI endpoints for the Bayesian calculator and legacy demo supervisor."""
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from fagan_nomogram import calculate_metrics
from .base import AuditLogger
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Fagan Nomogram Bayesian Updater API",
    description="Bayesian diagnostic calculations and separate illustrative supervisor endpoints.",
    version="3.1.0",
)


class FaganRequest(BaseModel):
    pretest_probability: float
    likelihood_ratio: float | None = None
    sensitivity: float | None = None
    specificity: float | None = None
    result: str = "positive"


class ChatRequest(BaseModel):
    query: str


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(Path(__file__).resolve().parent.parent / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "service": "fagan-nomogram-bayesian-updater", "version": "3.1.0"}


@app.post("/api/calculate")
def api_calculate(payload: FaganRequest):
    try:
        return calculate_metrics(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "DEMO_SUPERVISOR_AVAILABLE"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
