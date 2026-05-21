"""
MediBot AI — RAG (Retrieval-Augmented Generation) Engine
LangChain + FAISS vector store for medical knowledge retrieval
"""

import logging
import os
from typing import List, Optional, Dict
from pathlib import Path

logger = logging.getLogger("medibot.rag")


class RAGEngine:
    """
    Retrieval-Augmented Generation engine.
    Uses FAISS for vector similarity search over medical knowledge base.
    Gracefully degrades if dependencies are missing.
    """

    def __init__(self):
        self.available = False
        self.vectorstore = None
        self.embeddings = None
        self._init_rag()

    def _init_rag(self):
        try:
            from langchain_community.vectorstores import FAISS
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            from core.config import settings

            self._FAISS = FAISS
            self._splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
            )

            vector_path = Path(settings.VECTOR_DB_PATH)
            if vector_path.exists():
                self.vectorstore = FAISS.load_local(
                    str(vector_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
                logger.info("✅ RAG vectorstore loaded from disk")
            else:
                self._build_default_knowledge_base()

            self.available = True

        except ImportError as e:
            logger.warning(f"⚠️ RAG dependencies not installed: {e}. Running without RAG.")
        except Exception as e:
            logger.error(f"RAG init error: {e}")

    def _build_default_knowledge_base(self):
        """Build vectorstore from embedded medical knowledge."""
        from langchain.schema import Document

        docs = [Document(page_content=chunk, metadata={"source": meta})
                for chunk, meta in MEDICAL_KNOWLEDGE_CHUNKS]

        self.vectorstore = self._FAISS.from_documents(docs, self.embeddings)

        from core.config import settings
        os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
        self.vectorstore.save_local(settings.VECTOR_DB_PATH)
        logger.info("✅ RAG vectorstore built and saved")

    async def retrieve(self, query: str, k: int = 3) -> Optional[str]:
        """Retrieve relevant medical context for a query."""
        if not self.available or not self.vectorstore:
            return None
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            if not docs:
                return None
            context = "\n\n".join(
                f"[Source: {d.metadata.get('source', 'Medical KB')}]\n{d.page_content}"
                for d in docs
            )
            return context
        except Exception as e:
            logger.error(f"RAG retrieval error: {e}")
            return None

    def add_documents(self, texts: List[str], metadatas: List[Dict] = None):
        """Add new documents to the vectorstore."""
        if not self.available:
            return False
        try:
            from langchain.schema import Document
            docs = [
                Document(page_content=t, metadata=metadatas[i] if metadatas else {})
                for i, t in enumerate(texts)
            ]
            self.vectorstore.add_documents(docs)
            from core.config import settings
            self.vectorstore.save_local(settings.VECTOR_DB_PATH)
            return True
        except Exception as e:
            logger.error(f"RAG add_documents error: {e}")
            return False


# ─── Embedded Medical Knowledge Base ─────────────────────────────────────────
MEDICAL_KNOWLEDGE_CHUNKS = [
    ("Fever is a temporary increase in body temperature, often due to an illness. A fever is generally 38°C (100.4°F) or higher. Fever is a sign that the body is fighting an infection. Common causes: viral infections (flu, cold, COVID-19), bacterial infections (pneumonia, UTI), heat exhaustion. Management: stay hydrated, rest, paracetamol/ibuprofen. Seek care if >39.4°C (103°F) in adults, or any fever in infants under 3 months.", "General/Fever"),

    ("Diabetes mellitus type 2 is a chronic condition affecting how the body metabolizes sugar. Symptoms: increased thirst, frequent urination, fatigue, blurred vision, slow-healing wounds, numbness/tingling in feet. Risk factors: obesity, sedentary lifestyle, family history, age >45. Management: diet control (low glycemic index foods), regular exercise, weight loss, oral hypoglycemics (metformin), insulin if needed. Monitor HbA1c every 3 months. Target: HbA1c <7%, fasting glucose 80-130 mg/dL.", "Endocrine/Diabetes"),

    ("Hypertension (high blood pressure) is blood pressure consistently ≥130/80 mmHg. Often asymptomatic (silent killer). Risk factors: obesity, high salt intake, smoking, alcohol, stress, family history, age. Complications: stroke, heart attack, kidney disease, vision loss. Lifestyle modifications: DASH diet, reduce sodium to <2.3g/day, regular aerobic exercise, limit alcohol, quit smoking. Medications: ACE inhibitors, ARBs, calcium channel blockers, thiazide diuretics.", "Cardiovascular/Hypertension"),

    ("Asthma is a chronic inflammatory airway disease causing recurrent episodes of wheezing, breathlessness, chest tightness, and cough. Triggers: allergens (pollen, dust mites, pet dander), exercise, cold air, smoke, stress. Management: avoid triggers, short-acting beta-agonists (salbutamol) for rescue, inhaled corticosteroids for maintenance. Peak flow monitoring helps track control. Asthma action plan should be followed during attacks.", "Respiratory/Asthma"),

    ("COVID-19 caused by SARS-CoV-2. Symptoms: fever, dry cough, fatigue, loss of taste/smell, shortness of breath. Most cases are mild; high-risk groups (elderly, immunocompromised, comorbidities) may develop severe disease. Prevention: vaccination, masking in high-risk settings, hand hygiene, ventilation. Treatment: supportive care, antiviral medications (nirmatrelvir/ritonavir, remdesivir) for high-risk patients. Monitor SpO2; seek care if <94%.", "Infectious/COVID-19"),

    ("Malaria is a life-threatening disease caused by Plasmodium parasites transmitted by infected female Anopheles mosquitoes. Symptoms: cyclical fever, chills, sweating, headache, muscle pain, nausea. Diagnosis: rapid antigen test or blood smear microscopy. Treatment: artemisinin-based combination therapy (ACT). Prevention: insecticide-treated bed nets, indoor residual spraying, antimalarial prophylaxis for travelers, eliminate standing water.", "Infectious/Malaria"),

    ("Depression is a common and serious medical illness characterized by persistent sadness and loss of interest. Symptoms: depressed mood most of the day, diminished interest, significant weight change, insomnia or hypersomnia, fatigue, feelings of worthlessness, difficulty concentrating, recurrent thoughts of death. Treatment: psychotherapy (CBT), antidepressants (SSRIs, SNRIs), lifestyle changes (exercise, social support, sleep hygiene). Seek help if thoughts of self-harm occur. Crisis line: 988 (US), iCall: 9152987821 (India).", "Mental Health/Depression"),

    ("Urinary Tract Infections (UTIs) are bacterial infections of the urinary system. More common in women. Symptoms: burning urination, frequent urge to urinate, cloudy or blood-tinged urine, pelvic pain, strong urine odor. Upper UTI (pyelonephritis) adds fever, back pain, nausea. Diagnosis: urine culture. Treatment: antibiotics (trimethoprim-sulfamethoxazole, nitrofurantoin, ciprofloxacin). Prevention: hydration, urinate after intercourse, front-to-back wiping, avoid irritants.", "Urological/UTI"),

    ("Migraine is a neurological disorder causing recurring moderate-to-severe headache, typically one-sided, pulsating, lasting 4-72 hours. Accompanied by nausea, vomiting, photophobia, phonophobia. Prodrome: mood changes, food cravings, neck stiffness. Aura (in ~30%): visual disturbances, numbness, speech difficulty. Triggers: stress, hormonal changes, specific foods (tyramine, caffeine, alcohol), sleep disruption, weather. Acute treatment: triptans, NSAIDs, antiemetics. Prevention: beta-blockers, topiramate, valproate, CGRP antagonists.", "Neurological/Migraine"),

    ("GERD (Gastroesophageal Reflux Disease) occurs when stomach acid repeatedly flows back into the esophagus. Symptoms: heartburn (burning chest pain), regurgitation of food/sour liquid, difficulty swallowing, chest pain, hoarseness, chronic cough. Aggravated by: large meals, fatty/spicy foods, coffee, alcohol, lying down after eating, obesity, smoking. Management: lifestyle changes, H2 blockers, proton pump inhibitors (omeprazole). Avoid eating 3 hours before bed. Surgery (fundoplication) for refractory cases.", "Gastrointestinal/GERD"),

    ("Anemia is a condition where you lack enough healthy red blood cells to carry adequate oxygen to body tissues. Types: iron deficiency (most common), vitamin B12/folate deficiency, hemolytic, aplastic. Symptoms: fatigue, weakness, pale skin, shortness of breath, dizziness, cold hands/feet, brittle nails, pica. Diagnosis: CBC, peripheral smear, ferritin, B12 levels. Treatment depends on type: iron supplements, B12 injections, folate, treating underlying cause.", "Hematological/Anemia"),

    ("Dengue fever is a mosquito-borne viral infection. Symptoms: sudden high fever, severe headache, pain behind eyes (retro-orbital), joint and muscle pain (breakbone fever), rash, mild bleeding. Warning signs of severe dengue: abdominal pain, persistent vomiting, rapid breathing, bleeding gums, blood in vomit. No specific antiviral. Treatment: supportive care, oral rehydration, paracetamol (avoid NSAIDs/aspirin). Monitor platelet count. Platelet transfusion if <10,000 or active bleeding.", "Infectious/Dengue"),

    ("Thyroid disorders: Hypothyroidism (underactive) - fatigue, weight gain, cold intolerance, constipation, dry skin, depression, bradycardia. Hyperthyroidism (overactive) - weight loss, heat intolerance, palpitations, tremor, anxiety, diarrhea. Diagnosis: TSH (primary screening), Free T3, Free T4. Hypothyroidism treatment: levothyroxine. Hyperthyroidism: antithyroid drugs (methimazole, propylthiouracil), radioactive iodine, surgery.", "Endocrine/Thyroid"),

    ("First Aid for Emergencies: Chest Pain/Heart Attack - call 911, rest, loosen tight clothing, chew aspirin 325mg if not allergic, begin CPR if unconscious. Stroke (FAST): Face drooping, Arm weakness, Speech difficulty, Time to call 911. Severe Bleeding: apply direct pressure, elevate limb, use tourniquet if needed. Burns: cool running water 20 mins, cover loosely, do not pop blisters. Choking (conscious adult): 5 back blows, 5 abdominal thrusts (Heimlich). Anaphylaxis: epinephrine auto-injector (EpiPen), call 911.", "Emergency/FirstAid"),

    ("Nutrition and healthy diet guidelines: Eat a variety of colorful fruits and vegetables (5 servings/day). Choose whole grains over refined. Limit saturated fats, trans fats, added sugars, sodium. Adequate protein: lean meats, legumes, eggs, dairy. Healthy fats: olive oil, nuts, avocado, fatty fish (omega-3). Hydration: 8-10 glasses water/day. Limit processed foods, sugary beverages, alcohol. Mediterranean diet reduces cardiovascular risk by ~30%.", "General/Nutrition"),

    ("Exercise and physical activity recommendations (WHO): Adults: 150-300 min moderate aerobic activity/week OR 75-150 min vigorous/week. Muscle-strengthening activities: 2+ days/week. Reduce sedentary behavior. Benefits: reduces cardiovascular disease risk by 35%, type 2 diabetes by 50%, depression by 30%, all-cause mortality by 30%. Types: cardio (walking, running, swimming), strength training, flexibility (yoga, stretching), balance exercises.", "General/Exercise"),
]


# Singleton
rag_engine = RAGEngine()
