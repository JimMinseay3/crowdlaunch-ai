import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import AgentRun, Approval, SessionLocal, init_db
from .providers import enrich_with_optional_model
from .schemas import AgentRunResponse, ApprovalRequest, BackerRequest, EnrichmentRequest, GrowthRequest, ResearchRequest
from .services import analyze_backers, diagnose_growth, run_research


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="CrowdLaunch AI API",
    version="0.1.0",
    description="No-key demo API for crowdfunding research, growth diagnosis, and Backer insights.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def record_run(db: Session, agent_type: str, project_name: str, payload: dict, output: dict) -> AgentRun:
    run = AgentRun(
        agent_type=agent_type,
        project_name=project_name,
        status="completed",
        input_json=json.dumps(payload, ensure_ascii=False),
        output_json=json.dumps(output, ensure_ascii=False),
        warning_count=len(output.get("warnings", [])),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_provider": "deterministic-demo", "external_writes": False}


@app.post("/api/research", response_model=AgentRunResponse)
def research(payload: ResearchRequest, db: Session = Depends(get_db)):
    output = run_research(payload)
    run = record_run(db, "research", payload.project_name, payload.model_dump(), output)
    return {"run_id": run.id, "agent_type": run.agent_type, "status": run.status, "output": output}


@app.post("/api/growth/diagnose", response_model=AgentRunResponse)
def growth(payload: GrowthRequest, db: Session = Depends(get_db)):
    output = diagnose_growth(payload.metrics)
    run = record_run(db, "growth", payload.project_name, payload.model_dump(), output)
    return {"run_id": run.id, "agent_type": run.agent_type, "status": run.status, "output": output}


@app.post("/api/backers/analyze", response_model=AgentRunResponse)
def backers(payload: BackerRequest, db: Session = Depends(get_db)):
    output = analyze_backers(payload)
    run = record_run(db, "backer_voice", payload.project_name, payload.model_dump(), output)
    return {"run_id": run.id, "agent_type": run.agent_type, "status": run.status, "output": output}


@app.get("/api/runs")
def runs(db: Session = Depends(get_db)):
    records = db.scalars(select(AgentRun).order_by(AgentRun.id.desc()).limit(50)).all()
    return [
        {
            "id": record.id,
            "agent_type": record.agent_type,
            "project_name": record.project_name,
            "status": record.status,
            "warning_count": record.warning_count,
            "created_at": record.created_at,
        }
        for record in records
    ]


@app.post("/api/model/enrich")
def model_enrich(payload: EnrichmentRequest):
    return enrich_with_optional_model(payload.task, payload.deterministic_result)


@app.post("/api/approvals/{recommendation_id}")
def approve(recommendation_id: str, payload: ApprovalRequest, db: Session = Depends(get_db)):
    item = db.scalar(select(Approval).where(Approval.recommendation_id == recommendation_id))
    if item and item.status == "approved":
        raise HTTPException(status_code=409, detail="Recommendation already approved")
    if not item:
        item = Approval(recommendation_id=recommendation_id)
        db.add(item)
    item.status = "approved"
    item.approved_by = payload.approved_by
    item.approved_at = datetime.now(timezone.utc)
    db.commit()
    return {
        "recommendation_id": recommendation_id,
        "status": "approved",
        "external_action_executed": False,
    }
