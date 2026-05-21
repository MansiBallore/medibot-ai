"""
MediBot AI — Diagnosis API
ML-based disease prediction, diagnosis history, severity scoring
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid

from core.auth import get_current_user
from core.database import db_insert, db_find_many
from ml.disease_predictor import predict_from_text, check_emergency

router = APIRouter()


class DiagnosisRequest(BaseModel):
    symptoms: str = Field(..., min_length=3, max_length=1000)
    patient_age: Optional[int] = Field(None, ge=1, le=120)
    patient_gender: Optional[str] = None
    duration_days: Optional[int] = None
    existing_conditions: Optional[List[str]] = []


class BatchDiagnosisRequest(BaseModel):
    symptom_list: List[str] = Field(..., min_items=1, max_items=20)


@router.post("/predict")
async def predict_diagnosis(
    body: DiagnosisRequest,
    user: dict = Depends(get_current_user),
):
    """
    Run ML disease prediction from symptom description.
    Returns ranked predictions with confidence scores.
    """
    result = predict_from_text(body.symptoms)
    is_emergency = check_emergency(body.symptoms)

    # Save to history
    record = {
        "_id": str(uuid.uuid4()),
        "user_id": user.get("user_id", "guest"),
        "symptoms_text": body.symptoms,
        "patient_age": body.patient_age,
        "patient_gender": body.patient_gender,
        "duration_days": body.duration_days,
        "existing_conditions": body.existing_conditions,
        "predictions": result["predictions"],
        "is_emergency": is_emergency,
        "extracted_symptoms": result.get("extracted_symptoms", []),
    }
    record_id = await db_insert("diagnoses", record)

    return {
        "diagnosis_id": record_id,
        "is_emergency": is_emergency,
        "predictions": result["predictions"],
        "extracted_symptoms": result.get("extracted_symptoms", []),
        "response": result["response"],
    }


@router.get("/history")
async def get_diagnosis_history(
    user: dict = Depends(get_current_user),
    limit: int = 20,
):
    """Retrieve diagnosis history for the current user."""
    user_id = user.get("user_id", "guest")
    records = await db_find_many("diagnoses", {"user_id": user_id}, limit=limit)
    return {"history": records, "count": len(records)}


@router.get("/diseases")
async def list_diseases():
    """List all diseases in the knowledge base."""
    from ml.disease_predictor import DISEASE_KB
    diseases = [
        {
            "key": key,
            "name": key.replace("_", " ").title(),
            "category": info["category"],
            "icd10": info.get("icd10", ""),
            "severity": info["severity"],
            "symptoms": info["symptoms"],
        }
        for key, info in DISEASE_KB.items()
    ]
    return {
        "total": len(diseases),
        "diseases": sorted(diseases, key=lambda d: d["category"]),
    }


@router.post("/batch")
async def batch_predict(body: BatchDiagnosisRequest):
    """Predict for multiple symptom strings at once."""
    results = []
    for symptom_text in body.symptom_list:
        r = predict_from_text(symptom_text)
        results.append({
            "input": symptom_text,
            "predictions": r["predictions"][:3],
            "is_emergency": r["is_emergency"],
        })
    return {"results": results}
