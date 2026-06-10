from fastapi import FastAPI, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json

from models import User, Incident, get_db
from auth import router as auth_router, get_current_user
from agents.monitor import MonitorAgent
from agents.diagnosis import DiagnosisAgent
from agents.remediation import RemediationAgent

app = FastAPI(title="AegisAI Backend")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth Router
app.include_router(auth_router)

# Initialize Agents
monitor = MonitorAgent()
diagnosis = DiagnosisAgent()
remediation = RemediationAgent()

class IncidentRequest(BaseModel):
    logs: list[str]

@app.post("/diagnose")
async def diagnose_incident(
    request: IncidentRequest, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Full diagnosis pipeline (Protected)"""
    anomaly = monitor.detect_anomaly(request.logs)
    if not anomaly.get("anomaly_detected"):
        return {"status": "ok", "anomaly_detected": False}
        
    root_cause = diagnosis.analyze_root_cause(anomaly, request.logs)
    remed_plan = remediation.suggest_remediation(anomaly, root_cause)
    
    # Save the input logs
    log_text = "\n".join(request.logs)
    
    new_incident = Incident(
        user_id=current_user.id,
        raw_logs=log_text,
        status="open",
        anomaly_description=f"Type: {anomaly.get('anomaly_type')} | Severity: {anomaly.get('severity')}",
        root_cause=root_cause.get("root_cause"),
        remediation_action=", ".join(remed_plan.get("immediate_actions", [])),
        remediation_status="pending"
    )
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)
    
    return {
        "incident_id": new_incident.id,
        "anomaly": anomaly,
        "root_cause": root_cause,
        "remediation": remed_plan
    }

@app.get("/my-incidents")
async def get_user_incidents(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Get all incidents specific to the logged-in user"""
    incidents = db.query(Incident).filter(
        Incident.user_id == current_user.id
    ).order_by(Incident.timestamp.desc()).all()
    
    return [{
        "id": i.id, 
        "timestamp": i.timestamp, 
        "raw_logs": i.raw_logs, 
        "anomaly": i.anomaly_description, 
        "root_cause": i.root_cause,
        "remediation": i.remediation_action,
        "status": i.status
    } for i in incidents]

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)