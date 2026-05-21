import os

content = '''"""
MediBot AI — Core Generative AI Engine
Supports: Gemini, OpenAI, Groq, with intelligent fallback
"""

import logging
import json
import os
from typing import List, Dict, Optional, AsyncGenerator
from core.config import settings

logger = logging.getLogger("medibot.ai_engine")

SYSTEM_PROMPT = """You are MediBot, an advanced AI Healthcare Assistant. Your role is to:

1. Help users understand their symptoms with empathy and clarity
2. Provide evidence-based health information and guidance
3. Ask intelligent follow-up questions to better understand the situation
4. Detect emergency symptoms and immediately advise seeking urgent care
5. Provide actionable, practical health advice
6. Always remind users you are an AI and not a substitute for professional medical care

CRITICAL RULES:
- If symptoms suggest a medical emergency (chest pain, difficulty breathing, severe bleeding, stroke signs, anaphylaxis), IMMEDIATELY advise calling emergency services (911/112)
- Never diagnose definitively - use may indicate, could be, suggests
- Always recommend consulting a doctor for serious or persistent symptoms
- Be compassionate, clear, and non-alarmist
- Ask follow-up questions to gather more context when needed
- Provide confidence levels for your assessments

RESPONSE FORMAT:
- Use clear headings and bullet points
- Include severity assessment: LOW / MEDIUM / HIGH / EMERGENCY
- Include confidence score (0-100%)
- Always end with a recommendation
"""


class AIEngine:
    def __init__(self):
        self.provider = os.environ.get("AI_PROVIDER", settings.AI_PROVIDER)
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            groq_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
            gemini_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
            openai_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")

            print(f"DEBUG provider={self.provider} groq_key={bool(groq_key)} gemini_key={bool(gemini_key)}")

            if self.provider == "openai" and openai_key:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=openai_key)
                logger.info("✅ OpenAI client initialized")

            elif self.provider == "groq" and groq_key:
                from groq import AsyncGroq
                self._client = AsyncGroq(api_key=groq_key)
                self.provider = "groq"
                logger.info("✅ Groq client initialized")

            elif gemini_key:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                self._client = genai.GenerativeModel(
                    model_name=settings.AI_MODEL or "gemini-1.5-flash",
                    system_instruction=SYSTEM_PROMPT,
                )
                self.provider = "gemini"
                logger.info("✅ Gemini client initialized")

            else:
                logger.warning("⚠️ No AI API key configured — using rule-based fallback")
                self.provider = "fallback"

        except ImportError as e:
            logger.warning(f"⚠️ AI library not installed: {e} — using fallback")
            self.provider = "fallback"

    async def chat(self, messages, context=None, temperature=0.3):
        if context:
            messages = messages.copy()
            messages[-1]["content"] = (
                f"Relevant medical context:\n{context}\n\n"
                f"User query: {messages[-1][\"content\"]}"
            )
        try:
            if self.provider == "openai":
                return await self._openai_chat(messages, temperature)
            elif self.provider == "groq":
                return await self._groq_chat(messages, temperature)
            elif self.provider == "gemini":
                return await self._gemini_chat(messages, temperature)
            else:
                return self._fallback_response(messages[-1]["content"])
        except Exception as e:
            logger.error(f"AI engine error: {e}")
            return self._fallback_response(messages[-1]["content"])

    async def _openai_chat(self, messages, temperature):
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        response = await self._client.chat.completions.create(
            model=settings.AI_MODEL or "gpt-4o-mini",
            messages=full_messages,
            temperature=temperature,
            max_tokens=1024,
        )
        return {"reply": response.choices[0].message.content, "provider": "openai", "model": settings.AI_MODEL}

    async def _groq_chat(self, messages, temperature):
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        response = await self._client.chat.completions.create(
            model=settings.AI_MODEL or "llama3-8b-8192",
            messages=full_messages,
            temperature=temperature,
            max_tokens=1024,
        )
        return {"reply": response.choices[0].message.content, "provider": "groq", "model": settings.AI_MODEL}

    async def _gemini_chat(self, messages, temperature):
        history = []
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})
        chat = self._client.start_chat(history=history)
        response = await chat.send_message_async(
            messages[-1]["content"],
            generation_config={"temperature": temperature, "max_output_tokens": 1024},
        )
        return {"reply": response.text, "provider": "gemini", "model": settings.AI_MODEL}

    def _fallback_response(self, user_message):
        from ml.disease_predictor import predict_from_text
        result = predict_from_text(user_message)
        return {"reply": result["response"], "provider": "fallback", "model": "rule-based"}

    async def extract_symptoms_ai(self, text):
        prompt = f"""Extract medical symptoms from this text. Return JSON only.
Text: "{text}"
Return format:
{{"symptoms": ["symptom1"], "duration": null, "severity": "unknown", "body_parts": [], "associated_factors": []}}"""
        try:
            result = await self.chat([{"role": "user", "content": prompt}], temperature=0.1)
            t = result["reply"].strip()
            if "`" in t:
                t = t.split("`")[1]
                if t.startswith("json"):
                    t = t[4:]
            return json.loads(t.strip())
        except Exception as e:
            logger.error(f"Symptom extraction error: {e}")
            return {"symptoms": [], "duration": None, "severity": "unknown", "body_parts": [], "associated_factors": []}


ai_engine = AIEngine()
'''

with open('backend/core/ai_engine.py', 'w') as f:
    f.write(content)
print('ai_engine.py restored successfully!')
