# MediBot AI — API Reference

> Interactive docs available at: `http://localhost:8000/api/docs`

---

## Base URL
```
http://localhost:8000/api
```

## Authentication
Most endpoints accept an optional JWT Bearer token. Unauthenticated requests are served as "guest".

```
Authorization: Bearer <token>
```

---

## Auth Endpoints

### POST `/auth/register`
Register a new user account.

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepass",
  "full_name": "John Doe",
  "age": 30,
  "gender": "male"
}
```

**Response:**
```json
{
  "message": "Registration successful",
  "token": "eyJ...",
  "user": { "user_id": "...", "username": "johndoe", "email": "john@example.com" }
}
```

---

### POST `/auth/login`
```json
{ "email": "john@example.com", "password": "securepass" }
```

---

### POST `/auth/guest-token`
Issue a temporary guest token (no body required).

---

### GET `/auth/me`
Returns the authenticated user's profile.

---

## Chat Endpoints

### POST `/chat/send`
Main chat endpoint. Returns AI response with predictions.

**Request Body:**
```json
{
  "message": "I have fever, cough, and body pain for 2 days",
  "session_id": "optional-existing-session-id",
  "use_rag": true
}
```

**Response:**
```json
{
  "reply": "## 🟡 Most Likely: Flu\n\n...",
  "session_id": "uuid",
  "message_id": "uuid",
  "provider": "gemini",
  "is_emergency": false,
  "predictions": [
    {
      "disease": "flu",
      "display_name": "Flu",
      "confidence": 78.5,
      "severity": "medium",
      "category": "Respiratory",
      "matched_symptoms": ["fever", "cough", "body pain"],
      "icd10": "J10"
    }
  ],
  "extracted_symptoms": ["fever", "cough", "body pain"],
  "rag_used": true
}
```

---

### GET `/chat/sessions`
List all sessions for the current user.

### POST `/chat/sessions`
```json
{ "title": "My Headache Consultation" }
```

### GET `/chat/sessions/{session_id}/history`
Returns all messages in a session.

### DELETE `/chat/sessions/{session_id}`
Delete a session.

### POST `/chat/feedback`
```json
{ "message_id": "uuid", "rating": 5, "comment": "Very helpful!" }
```

---

## Diagnosis Endpoints

### POST `/diagnosis/predict`
Run ML-only disease prediction (no AI generation).

**Request Body:**
```json
{
  "symptoms": "fever, joint pain, rash after mosquito bite",
  "patient_age": 28,
  "patient_gender": "female",
  "duration_days": 3,
  "existing_conditions": ["diabetes"]
}
```

**Response:**
```json
{
  "diagnosis_id": "uuid",
  "is_emergency": false,
  "predictions": [...],
  "extracted_symptoms": ["fever", "joint pain", "rash"],
  "response": "## 🔴 Most Likely: Dengue Fever\n..."
}
```

### GET `/diagnosis/history`
Returns the user's past diagnoses.

### GET `/diagnosis/diseases`
Returns the full disease knowledge base (40+ diseases).

### POST `/diagnosis/batch`
Run predictions for multiple symptom texts at once.
```json
{
  "symptom_list": [
    "fever and cough",
    "burning urination and frequent urge"
  ]
}
```

---

## OCR Endpoints

### POST `/ocr/prescription`
Upload a prescription image (JPEG/PNG/WEBP).
- **Form field:** `file`
- **Returns:** `extracted_text`, `analysis` (AI interpretation)

### POST `/ocr/report`
Upload a medical report (PDF or image).
- **Form field:** `file`
- **Returns:** `extracted_text`, `analysis` (AI plain-language summary)

---

## Analytics Endpoints

### GET `/analytics/dashboard`
Returns personalized analytics for the current user.

**Response:**
```json
{
  "stats": {
    "total_chats": 42,
    "total_diagnoses": 18,
    "total_sessions": 7,
    "diseases_in_kb": 40
  },
  "top_diseases": [
    { "disease": "Flu", "count": 5 },
    { "disease": "UTI", "count": 3 }
  ],
  "severity_distribution": { "low": 8, "medium": 7, "high": 3 },
  "disease_categories": { "Respiratory": 6, "Infectious": 5, ... }
}
```

### GET `/analytics/global`
Global platform statistics (anonymized).

---

## Health Check

### GET `/api/health`
```json
{ "status": "healthy", "version": "2.0.0", "service": "MediBot AI" }
```

---

## Error Responses

All errors follow:
```json
{ "detail": "Error message here" }
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request / validation error |
| 401 | Unauthorized (invalid/missing token) |
| 404 | Resource not found |
| 409 | Conflict (e.g. email already registered) |
| 413 | File too large |
| 422 | Unprocessable entity (schema error) |
| 500 | Internal server error |
