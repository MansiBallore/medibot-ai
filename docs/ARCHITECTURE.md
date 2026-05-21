# MediBot AI — Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT BROWSER                           │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│   │ Chat UI  │  │Analytics │  │ OCR Tab  │  │Voice/Speech  │  │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
└────────┼─────────────┼─────────────┼────────────────┼──────────┘
         │             │             │                │
         └─────────────┴─────────────┴────────────────┘
                                │
                       HTTP REST / JSON
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                    FASTAPI BACKEND                               │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  /api/auth   │  │  /api/chat   │  │  /api/diagnosis      │  │
│  │  - register  │  │  - send      │  │  - predict (ML)      │  │
│  │  - login     │  │  - sessions  │  │  - history           │  │
│  │  - guest     │  │  - history   │  │  - diseases          │  │
│  └──────────────┘  └──────┬───────┘  └──────────────────────┘  │
│                            │                                     │
│  ┌──────────────┐  ┌───────▼───────────────────────────────┐   │
│  │  /api/ocr    │  │           CORE AI PIPELINE             │   │
│  │  - prescrip. │  │                                        │   │
│  │  - report    │  │  1. Emergency Detection                │   │
│  └──────────────┘  │  2. Symptom NLP Extraction            │   │
│                    │  3. ML Disease Prediction (40+ DB)     │   │
│  ┌──────────────┐  │  4. RAG Retrieval (FAISS)             │   │
│  │ /api/analyti │  │  5. AI Generation (Gemini/GPT/Groq)   │   │
│  │  - dashboard │  │  6. Response Assembly                  │   │
│  │  - global    │  └────────────────────────────────────────┘  │
│  └──────────────┘                                               │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               MIDDLEWARE STACK                           │   │
│  │   JWT Auth → CORS → GZip → Request Logger               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         │              │                  │
    ┌────▼────┐   ┌─────▼─────┐   ┌───────▼──────┐
    │ MongoDB │   │  FAISS    │   │  AI APIs     │
    │(Motor)  │   │VectorStore│   │  Gemini      │
    │         │   │           │   │  OpenAI      │
    │ In-mem  │   │ HuggingFace│  │  Groq        │
    │fallback │   │ Embeddings│   └──────────────┘
    └─────────┘   └───────────┘
```

## Data Flow: Chat Message

```
User types: "I have fever, headache, and joint pain"
                    │
                    ▼
        ┌───────────────────────┐
        │  Emergency Detection  │ ──► Safe (no emergency keywords)
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  NLP Token Extraction │ ──► ["fever", "headache", "joint pain"]
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐    ┌─────────────────────────────────┐
        │  ML Disease Scoring   │    │ Score each of 40+ diseases       │
        │  (disease_predictor)  │ ──►│ Dengue: 3/8 matches = 67%       │
        └───────────┬───────────┘    │ Flu: 3/9 matches = 55%          │
                    │                │ Malaria: 3/7 matches = 70%      │
                    ▼                └─────────────────────────────────┘
        ┌───────────────────────┐
        │   RAG Retrieval       │ ──► FAISS similarity search
        │   (LangChain+FAISS)   │     Returns relevant medical chunks
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   AI Generation       │ ──► Gemini / GPT / Groq / Fallback
        │   (ai_engine)         │     System prompt + conversation history
        │                       │     + ML context + RAG context
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   Response Assembly   │ ──► reply, predictions, rag_used, provider
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   DB Persist (bg)     │ ──► MongoDB / in-memory
        └───────────────────────┘
                    │
                    ▼
              JSON Response
```

## ML Prediction Algorithm

```python
confidence_score = min(0.95,
    matched_symptoms / total_disease_symptoms + 
    matched_count / 10
) * 100
```

Diseases are ranked by confidence score. Top-3 are returned.

## RAG Pipeline

```
User Query
    │
    ▼
HuggingFace sentence-transformers
(all-MiniLM-L6-v2 embeddings)
    │
    ▼
FAISS similarity_search(k=3)
    │
    ▼
Top-3 medical knowledge chunks
    │
    ▼
Injected as context into AI prompt
```

## AI Provider Fallback Chain

```
AI_PROVIDER=gemini ──► GEMINI_API_KEY exists? ──► Use Gemini
                                │ No
                                ▼
AI_PROVIDER=openai ──► OPENAI_API_KEY exists? ──► Use OpenAI GPT
                                │ No
                                ▼
AI_PROVIDER=groq   ──► GROQ_API_KEY exists?   ──► Use Groq Llama3
                                │ No
                                ▼
                        Rule-based ML fallback
                        (disease_predictor only)
```
