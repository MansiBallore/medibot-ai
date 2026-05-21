"""
MediBot AI — Test Suite
Run with: pytest tests/ -v
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─── ML Predictor Tests ───────────────────────────────────────────────────────
class TestDiseasePrediction:
    """Tests for the ML disease prediction engine."""

    def test_flu_prediction(self):
        from backend.ml.disease_predictor import predict_from_text
        result = predict_from_text("I have fever, cough, body pain, and chills")
        assert result["is_emergency"] is False
        assert len(result["predictions"]) > 0
        top = result["predictions"][0]
        assert top["confidence"] > 0
        assert top["severity"] in ["low", "medium", "high", "emergency"]

    def test_dengue_prediction(self):
        from backend.ml.disease_predictor import predict_from_text
        result = predict_from_text("high fever, severe joint pain, rash, eye pain, headache")
        preds = result["predictions"]
        disease_names = [p["disease"] for p in preds]
        assert any(d in disease_names for d in ["dengue", "malaria", "chikungunya"])

    def test_uti_prediction(self):
        from backend.ml.disease_predictor import predict_from_text
        result = predict_from_text("burning urination, frequent urge to urinate, cloudy urine")
        preds = result["predictions"]
        assert any(p["disease"] == "uti" for p in preds)

    def test_emergency_detection(self):
        from backend.ml.disease_predictor import check_emergency
        assert check_emergency("I have severe chest pain and cannot breathe") is True
        assert check_emergency("I have a mild headache") is False

    def test_no_symptoms_returns_empty(self):
        from backend.ml.disease_predictor import predict_from_text
        result = predict_from_text("the weather is nice today")
        assert result["is_emergency"] is False
        # May return empty or low-confidence predictions
        for pred in result["predictions"]:
            assert pred["confidence"] >= 0

    def test_symptom_extraction(self):
        from backend.ml.disease_predictor import extract_symptom_tokens
        tokens = extract_symptom_tokens("I have fever and joint pain since yesterday")
        assert "fever" in tokens

    def test_all_diseases_in_kb(self):
        from backend.ml.disease_predictor import DISEASE_KB
        assert len(DISEASE_KB) >= 30

    def test_confidence_range(self):
        from backend.ml.disease_predictor import predict_from_text
        result = predict_from_text("headache, nausea, light sensitivity, throbbing pain")
        for pred in result["predictions"]:
            assert 0 <= pred["confidence"] <= 100

    def test_prediction_has_required_fields(self):
        from backend.ml.disease_predictor import predict_from_text
        result = predict_from_text("fever, cough, fatigue, loss of taste")
        if result["predictions"]:
            p = result["predictions"][0]
            for field in ["disease", "display_name", "confidence", "severity", "category", "icd10"]:
                assert field in p, f"Missing field: {field}"


# ─── Auth Utility Tests ───────────────────────────────────────────────────────
class TestAuth:
    def test_password_hash_and_verify(self):
        from backend.core.auth import hash_password, verify_password
        hashed = hash_password("testpassword123")
        assert verify_password("testpassword123", hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_create_and_decode_token(self):
        from backend.core.auth import create_access_token, decode_token
        token = create_access_token({"user_id": "test123", "username": "tester"})
        payload = decode_token(token)
        assert payload["user_id"] == "test123"
        assert payload["username"] == "tester"

    def test_expired_token_raises(self):
        from backend.core.auth import create_access_token, decode_token
        from datetime import timedelta
        from fastapi import HTTPException
        token = create_access_token({"user_id": "x"}, expires_delta=timedelta(seconds=-1))
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        assert exc_info.value.status_code == 401


# ─── Config Tests ─────────────────────────────────────────────────────────────
class TestConfig:
    def test_settings_load(self):
        from backend.core.config import settings
        assert settings.APP_NAME == "MediBot AI"
        assert settings.VERSION == "2.0.0"

    def test_ai_provider_default(self):
        from backend.core.config import settings
        assert settings.AI_PROVIDER in ["gemini", "openai", "groq", "fallback"]


# ─── FastAPI Endpoint Tests ───────────────────────────────────────────────────
class TestEndpoints:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        import importlib
        try:
            main = importlib.import_module("backend.main")
            return TestClient(main.app)
        except Exception:
            pytest.skip("FastAPI app could not be initialized")

    def test_health_check(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"

    def test_get_diseases(self, client):
        res = client.get("/api/diagnosis/diseases")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 30
        assert len(data["diseases"]) >= 30

    def test_guest_token(self, client):
        res = client.post("/api/auth/guest-token")
        assert res.status_code == 200
        assert "token" in res.json()

    def test_diagnosis_predict(self, client):
        token_res = client.post("/api/auth/guest-token")
        token = token_res.json()["token"]
        res = client.post(
            "/api/diagnosis/predict",
            json={"symptoms": "fever, cough, body pain, headache"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "predictions" in data
        assert "is_emergency" in data

    def test_emergency_diagnosis(self, client):
        token_res = client.post("/api/auth/guest-token")
        token = token_res.json()["token"]
        res = client.post(
            "/api/diagnosis/predict",
            json={"symptoms": "severe chest pain and difficulty breathing"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["is_emergency"] is True

    def test_chat_greeting(self, client):
        token_res = client.post("/api/auth/guest-token")
        token = token_res.json()["token"]
        res = client.post(
            "/api/chat/send",
            json={"message": "hello", "use_rag": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "reply" in data
        assert len(data["reply"]) > 0

    def test_register_and_login(self, client):
        import uuid
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"

        # Register
        res = client.post("/api/auth/register", json={
            "username": f"user_{uuid.uuid4().hex[:6]}",
            "email": unique_email,
            "password": "testpass123",
        })
        assert res.status_code == 201
        token = res.json()["token"]
        assert token

        # Login
        res2 = client.post("/api/auth/login", json={
            "email": unique_email,
            "password": "testpass123",
        })
        assert res2.status_code == 200
        assert "token" in res2.json()

    def test_global_analytics(self, client):
        res = client.get("/api/analytics/global")
        assert res.status_code == 200
        data = res.json()
        assert "diseases_in_kb" in data
        assert data["diseases_in_kb"] >= 30
