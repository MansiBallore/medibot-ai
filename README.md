# 🏥 MediBot AI — Advanced Generative AI Healthcare Assistant

<div align="center">

![MediBot AI](https://img.shields.io/badge/MediBot-AI%20Healthcare-00d68f?style=for-the-badge&logo=heart)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi)
![AI Powered](https://img.shields.io/badge/AI-Gemini%20%7C%20GPT%20%7C%20Groq-orange?style=for-the-badge)

**Production-grade AI Healthcare Assistant for AI/ML internships, Full Stack AI roles, and startup portfolios.**

</div>

---

## 📌 Project Overview

MediBot AI is a fully-featured Generative AI Healthcare Assistant that combines:
- **Generative AI** (Gemini / OpenAI GPT / Groq Llama 3)
- **RAG** (Retrieval-Augmented Generation with FAISS vector store)
- **ML Disease Prediction** (40+ diseases, confidence scoring)
- **NLP Symptom Extraction**
- **OCR** (Prescription & Report analysis)
- **JWT Authentication** with multi-user support
- **Modern SaaS UI** with dark mode, voice input, analytics dashboard
- **Docker + Render deployment** ready

---

## 🚀 Features

### 🤖 Generative AI
- Multi-provider support: **Gemini 1.5 Flash**, **GPT-4o-mini**, **Groq Llama 3**
- Context-aware conversational memory (session-based)
- Advanced healthcare system prompt engineering
- Intelligent follow-up question generation
- Automatic AI provider fallback

### 🧠 ML & NLP
- **40+ diseases** across 11 medical categories
- Multi-symptom NLP extraction from natural language
- Confidence scoring (0–100%) per prediction
- Severity assessment: LOW / MEDIUM / HIGH / EMERGENCY
- ICD-10 codes for each disease
- Emergency symptom detection with immediate alerts

### 📚 RAG System
- LangChain + FAISS vector store
- HuggingFace sentence-transformers embeddings
- Medical knowledge base (16 domain chunks)
- Automatic vectorstore persistence
- Context-enriched AI responses

### 🎤 Voice & OCR
- Web Speech API voice input
- Tesseract OCR for prescription images
- pypdf for medical report analysis
- AI-powered prescription interpretation

### 🔐 Backend
- FastAPI with async/await throughout
- JWT authentication (register/login/guest)
- MongoDB via Motor async driver (with in-memory fallback)
- Modular REST API with OpenAPI/Swagger docs
- Request logging, GZIP compression
- Background task processing

### 🎨 Frontend
- Modern SaaS-like dark/light theme
- Responsive chat UI with typing animations
- Sidebar with session history
- Analytics dashboard with charts
- Drag-and-drop document upload
- Quick symptom chips

---

## 📁 Folder Structure

```
medibot-ai/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── api/
│   │   ├── auth.py             # JWT auth endpoints
│   │   ├── chat.py             # Chat & session endpoints
│   │   ├── diagnosis.py        # ML prediction endpoints
│   │   ├── analytics.py        # Dashboard endpoints
│   │   └── ocr.py              # OCR & document endpoints
│   ├── core/
│   │   ├── config.py           # Environment config (pydantic-settings)
│   │   ├── database.py         # MongoDB + in-memory DB layer
│   │   ├── auth.py             # JWT utilities
│   │   └── ai_engine.py        # Multi-provider AI engine
│   ├── ml/
│   │   └── disease_predictor.py # 40+ disease ML engine
│   └── rag/
│       └── rag_engine.py       # LangChain + FAISS RAG
├── frontend/
│   ├── templates/
│   │   └── index.html          # Jinja2 HTML template
│   └── static/
│       ├── css/main.css        # Production CSS
│       └── js/app.js           # Frontend application JS
├── data/
│   ├── vectorstore/            # FAISS index (auto-generated)
│   └── medical_docs/           # Optional custom docs
├── docs/
│   └── API.md                  # API reference
├── tests/
├── .env.example                # Environment template
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container build
├── docker-compose.yml          # Full stack compose
└── render.yaml                 # Render.com deployment
```

---

## ⚡ Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/yourusername/medibot-ai.git
cd medibot-ai

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

**Minimum required:** Add at least one AI API key:
```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_key_here   # Free at aistudio.google.com
```

### 3. Run
```bash
# From project root
uvicorn backend.main:app --reload --port 8000

# OR
cd backend && python main.py
```

Open **http://localhost:8000** in your browser.

API docs: **http://localhost:8000/api/docs**

---

## 🐳 Docker Deployment

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Start all services (app + MongoDB)
docker-compose up -d

# View logs
docker-compose logs -f medibot
```

---

## ☁️ Deploy to Render (Free)

1. Push project to GitHub
2. Connect repo at **render.com/new**
3. Select "Web Service"
4. Set Environment Variables (copy from `.env.example`)
5. Deploy — Render uses `render.yaml` automatically

---

## 🔑 AI API Keys (Get for Free)

| Provider | Model | Free Tier | Get Key |
|----------|-------|-----------|---------|
| **Gemini** | gemini-1.5-flash | ✅ 15 req/min free | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| **Groq** | llama3-8b-8192 | ✅ Very generous | [console.groq.com](https://console.groq.com/keys) |
| **OpenAI** | gpt-4o-mini | 💰 Paid ($0.15/1M tokens) | [platform.openai.com](https://platform.openai.com/api-keys) |

> **Recommended for getting started:** Gemini (free, fast, capable)

---

## 📡 API Reference

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/send` | Send message, get AI response |
| GET | `/api/chat/sessions` | List user sessions |
| POST | `/api/chat/sessions` | Create new session |
| GET | `/api/chat/sessions/{id}/history` | Get session messages |

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/me` | Get profile |
| POST | `/api/auth/guest-token` | Guest access |

### Diagnosis
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/diagnosis/predict` | ML disease prediction |
| GET | `/api/diagnosis/history` | Diagnosis history |
| GET | `/api/diagnosis/diseases` | List all diseases in KB |

### OCR
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ocr/prescription` | Analyze prescription image |
| POST | `/api/ocr/report` | Analyze PDF medical report |

Full interactive docs: `http://localhost:8000/api/docs`

---

## 🏥 Supported Diseases (40+)

| Category | Diseases |
|----------|---------|
| Respiratory | Flu, Common Cold, Bronchitis, Pneumonia, Asthma, COVID-19 |
| Infectious | Malaria, Dengue, Chikungunya, Typhoid, Food Poisoning |
| Gastrointestinal | Gastroenteritis, Acid Reflux, IBS |
| Cardiovascular | Hypertension |
| Neurological | Migraine, Tension Headache |
| Musculoskeletal | Arthritis, Back Pain |
| Dermatological | Chickenpox, Urticaria, Eczema |
| Endocrine | Type 2 Diabetes, Hypothyroidism |
| Urological | UTI, Kidney Stones |
| Mental Health | Anxiety, Depression, Insomnia |
| ENT | Sinusitis, Tonsillitis |
| Hematological | Anemia |
| Ophthalmological | Conjunctivitis |
| Reproductive | PCOS |

---

## 🔬 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, Python 3.11, Uvicorn |
| **AI/LLM** | Google Gemini, OpenAI, Groq |
| **RAG** | LangChain, FAISS, HuggingFace |
| **ML/NLP** | scikit-learn, NLTK, custom NLP |
| **Database** | MongoDB (Motor async), in-memory fallback |
| **Auth** | JWT (PyJWT), bcrypt |
| **OCR** | Tesseract, pypdf, Pillow |
| **Frontend** | Vanilla JS, CSS3, Web Speech API |
| **Deployment** | Docker, Docker Compose, Render |

---

## ⚠️ Disclaimer

MediBot AI is for **educational and informational purposes only**. It is NOT a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional for medical concerns.

---

## 📄 License

MIT License — free for personal, educational, and commercial use.

---

<div align="center">
Built with ❤️ for AI/ML portfolios and healthcare innovation
</div>
