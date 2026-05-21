"""
MediBot AI — Analytics API
Dashboard stats, usage metrics, disease trends
"""

from fastapi import APIRouter, Depends
from core.auth import get_current_user
from core.database import db_count, db_find_many
from ml.disease_predictor import DISEASE_KB
from collections import Counter

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(user: dict = Depends(get_current_user)):
    """Analytics dashboard data."""
    user_id = user.get("user_id", "guest")

    total_chats = await db_count("messages", {"user_id": user_id, "role": "user"})
    total_diagnoses = await db_count("diagnoses", {"user_id": user_id})
    total_sessions = await db_count("sessions", {"user_id": user_id})

    # Recent diagnoses for disease trend
    recent = await db_find_many("diagnoses", {"user_id": user_id}, limit=50)
    disease_counts = Counter()
    severity_counts = Counter()

    for record in recent:
        for pred in record.get("predictions", [])[:1]:
            disease_counts[pred.get("display_name", "Unknown")] += 1
            severity_counts[pred.get("severity", "unknown")] += 1

    top_diseases = [{"disease": k, "count": v} for k, v in disease_counts.most_common(5)]
    category_counts = Counter(info["category"] for info in DISEASE_KB.values())

    return {
        "stats": {
            "total_chats": total_chats,
            "total_diagnoses": total_diagnoses,
            "total_sessions": total_sessions,
            "diseases_in_kb": len(DISEASE_KB),
        },
        "top_diseases": top_diseases,
        "severity_distribution": dict(severity_counts),
        "disease_categories": dict(category_counts),
    }


@router.get("/global")
async def global_stats():
    """Global platform statistics (anonymized)."""
    total_users = await db_count("users", {})
    total_messages = await db_count("messages", {})
    total_diagnoses = await db_count("diagnoses", {})

    return {
        "total_users": total_users,
        "total_messages": total_messages,
        "total_diagnoses": total_diagnoses,
        "diseases_in_kb": len(DISEASE_KB),
        "version": "2.0.0",
    }
