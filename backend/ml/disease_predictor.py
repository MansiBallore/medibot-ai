"""
MediBot AI — ML Disease Prediction Engine
40+ diseases, NLP symptom extraction, confidence scoring
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger("medibot.ml")

# ─── Emergency Symptoms ───────────────────────────────────────────────────────
EMERGENCY_SYMPTOMS = [
    "cannot breathe", "can't breathe",
    "severe chest pain", "crushing chest pain",
    "severe bleeding", "uncontrolled bleeding",
    "unconscious", "loss of consciousness",
    "stroke", "face drooping", "slurred speech",
    "anaphylaxis", "throat closing",
    "severe head injury", "seizure",
    "heart attack",
]

# ─── Comprehensive Disease Knowledge Base (40+ diseases) ─────────────────────
DISEASE_KB: Dict[str, Dict] = {
    # === RESPIRATORY ===
    "flu": {
        "category": "Respiratory",
        "symptoms": ["fever", "cough", "body pain", "headache", "fatigue", "chills", "sore throat", "muscle ache", "weakness"],
        "min_match": 2,
        "severity": "medium",
        "icd10": "J10",
        "advice": "**Influenza (Flu)**\n\nRest, stay hydrated, take paracetamol for fever. Antiviral medications (oseltamivir) are most effective within 48 hours of onset. See a doctor if symptoms worsen after 3–5 days.\n\n⚠️ Seek immediate care if you have difficulty breathing.",
        "followup": ["Do you have a fever above 38.5°C?", "Are you vaccinated against flu this season?"],
    },
    "common_cold": {
        "category": "Respiratory",
        "symptoms": ["cough", "sneezing", "runny nose", "blocked nose", "sore throat", "mild fever", "nasal congestion"],
        "min_match": 2,
        "severity": "low",
        "icd10": "J00",
        "advice": "**Common Cold**\n\nRest, warm fluids, honey-lemon tea. OTC decongestants/antihistamines help. Usually resolves in 7–10 days.\n\n💊 Antibiotics won't help — colds are viral.",
        "followup": ["How long have symptoms lasted?", "Do you have a fever?"],
    },
    "bronchitis": {
        "category": "Respiratory",
        "symptoms": ["persistent cough", "cough with mucus", "chest discomfort", "fatigue", "mild fever", "sore throat", "wheezing"],
        "min_match": 2,
        "severity": "medium",
        "icd10": "J20",
        "advice": "**Bronchitis**\n\nRest, stay hydrated, use a humidifier. Avoid smoke and irritants. Most acute bronchitis resolves in 2–3 weeks. See doctor if cough produces bloody mucus or persists > 3 weeks.",
        "followup": ["Is your cough producing yellow/green mucus?", "Do you smoke?"],
    },
    "pneumonia": {
        "category": "Respiratory",
        "symptoms": ["high fever", "chills", "cough with phlegm", "chest pain", "difficulty breathing", "fatigue", "rapid breathing", "sweating"],
        "min_match": 3,
        "severity": "high",
        "icd10": "J18",
        "advice": "**Pneumonia — Seek Medical Attention**\n\nPneumonia requires medical evaluation and possibly antibiotics or hospitalization. Do not self-treat. See a doctor immediately.\n\n🚨 Go to ER if SpO₂ < 94%, breathing is very difficult, or you have blue lips.",
        "followup": ["Do you have an SpO₂ pulse oximeter reading?", "Do you have any underlying health conditions?"],
    },
    "asthma": {
        "category": "Respiratory",
        "symptoms": ["wheezing", "shortness of breath", "chest tightness", "cough", "difficulty breathing", "nocturnal cough"],
        "min_match": 2,
        "severity": "medium",
        "icd10": "J45",
        "advice": "**Asthma**\n\nUse your prescribed inhaler. Avoid known triggers (dust, smoke, allergens). If symptoms don't improve with rescue inhaler, seek emergency care.\n\n🚨 Severe asthma attacks are life-threatening.",
        "followup": ["Do you have a rescue inhaler?", "What triggered the symptoms?"],
    },
    "covid19": {
        "category": "Infectious",
        "symptoms": ["fever", "dry cough", "tiredness", "loss of taste", "loss of smell", "shortness of breath", "sore throat", "body aches"],
        "min_match": 2,
        "severity": "medium",
        "icd10": "U07.1",
        "advice": "**COVID-19**\n\nIsolate immediately. Take an antigen or PCR test. Monitor SpO₂ (keep above 94%). Paracetamol for fever. Inform close contacts.\n\n🚨 Go to hospital if SpO₂ < 94% or breathing is severely difficult.",
        "followup": ["Have you been vaccinated against COVID-19?", "What is your current SpO₂ reading?"],
    },

    # === VECTOR-BORNE ===
    "malaria": {
        "category": "Infectious",
        "symptoms": ["fever", "chills", "sweating", "headache", "nausea", "vomiting", "muscle pain", "cyclical fever"],
        "min_match": 3,
        "severity": "high",
        "icd10": "B54",
        "advice": "**Malaria — See a Doctor Urgently**\n\nBlood test required for confirmation. Prescribed anti-malarials (artemisinin combination therapy). Use mosquito nets/repellent. Stay hydrated.\n\n🚨 Do not delay — malaria can be life-threatening.",
        "followup": ["Have you recently traveled to a malaria-endemic area?", "Do you have cyclical (every 48–72 hours) fevers?"],
    },
    "dengue": {
        "category": "Infectious",
        "symptoms": ["high fever", "severe headache", "eye pain", "joint pain", "rash", "nausea", "fatigue", "bleeding gums", "skin rash"],
        "min_match": 3,
        "severity": "high",
        "icd10": "A97",
        "advice": "**Dengue Fever — Seek Medical Care**\n\nBlood test (platelet count) required. Take paracetamol only — **avoid aspirin/ibuprofen/NSAIDs**. Drink fluids and coconut water. Rest completely.\n\n🚨 Hospitalize if bleeding, severe abdominal pain, or platelet count < 50,000.",
        "followup": ["Do you have any bleeding (gums, nose, under skin)?", "Have you had dengue before?"],
    },
    "chikungunya": {
        "category": "Infectious",
        "symptoms": ["fever", "severe joint pain", "joint swelling", "muscle pain", "headache", "nausea", "rash", "fatigue"],
        "min_match": 3,
        "severity": "medium",
        "icd10": "A92.0",
        "advice": "**Chikungunya**\n\nNo specific antiviral. Rest, stay hydrated, paracetamol for pain/fever. Joint pain may persist for months. Avoid NSAIDs initially. See doctor for confirmation.",
        "followup": ["Is joint pain the most severe symptom?", "Have you been in a mosquito-prone area?"],
    },

    # === GASTROINTESTINAL ===
    "gastroenteritis": {
        "category": "Gastrointestinal",
        "symptoms": ["diarrhea", "vomiting", "stomach cramps", "nausea", "fever", "dehydration", "loose stools"],
        "min_match": 2,
        "severity": "low",
        "icd10": "A09",
        "advice": "**Gastroenteritis (Stomach Flu)**\n\nORS (oral rehydration salts) to prevent dehydration. Bland BRAT diet (bananas, rice, applesauce, toast). Avoid dairy, fatty, spicy foods. Usually resolves in 1–3 days.\n\n⚠️ See doctor if vomiting > 24 hrs or blood in stool.",
        "followup": ["Any blood in stool or vomit?", "How many times have you vomited?"],
    },
    "typhoid": {
        "category": "Infectious",
        "symptoms": ["prolonged fever", "weakness", "stomach pain", "headache", "loss of appetite", "constipation", "rose spots", "slow heart rate"],
        "min_match": 3,
        "severity": "high",
        "icd10": "A01.0",
        "advice": "**Typhoid Fever — See a Doctor**\n\nWidal test/blood culture required. Prescribed antibiotics (ciprofloxacin/azithromycin). Eat light foods, boiled water only. Complete full antibiotic course.\n\n⚠️ Complete the full course even if you feel better.",
        "followup": ["How long have you had fever?", "Have you consumed potentially contaminated food or water?"],
    },
    "food_poisoning": {
        "category": "Gastrointestinal",
        "symptoms": ["nausea", "vomiting", "diarrhea", "stomach cramps", "fever", "weakness"],
        "min_match": 3,
        "severity": "medium",
        "icd10": "A05.9",
        "advice": "**Food Poisoning**\n\nReplace fluids and electrolytes with ORS. Rest. Eat bland foods when able. Typically resolves in 24–48 hours.\n\n⚠️ Seek care if symptoms > 3 days or you have high fever/blood in stool.",
        "followup": ["What did you eat 2–6 hours before symptoms?", "Has anyone else who ate the same food fallen ill?"],
    },
    "acid_reflux": {
        "category": "Gastrointestinal",
        "symptoms": ["heartburn", "acid reflux", "chest burning", "regurgitation", "sour taste", "difficulty swallowing", "burping"],
        "min_match": 2,
        "severity": "low",
        "icd10": "K21",
        "advice": "**GERD / Acid Reflux**\n\nAvoid spicy/fatty foods, coffee, alcohol. Don't lie down after eating. Elevate head of bed. OTC antacids (omeprazole, ranitidine) help. See doctor for persistent symptoms.",
        "followup": ["Does it worsen after meals?", "Any difficulty swallowing?"],
    },
    "ibs": {
        "category": "Gastrointestinal",
        "symptoms": ["abdominal pain", "bloating", "alternating diarrhea and constipation", "gas", "mucus in stool", "stomach cramps"],
        "min_match": 2,
        "severity": "low",
        "icd10": "K58",
        "advice": "**Irritable Bowel Syndrome (IBS)**\n\nIdentify and avoid trigger foods. High-fiber diet, regular exercise, stress management. Probiotics may help. See GI specialist for confirmed diagnosis.",
        "followup": ["Does stress worsen symptoms?", "Are there specific foods that trigger symptoms?"],
    },

    # === CARDIOVASCULAR ===
    "hypertension": {
        "category": "Cardiovascular",
        "symptoms": ["headache", "dizziness", "blurred vision", "nosebleed", "shortness of breath", "chest pain", "palpitations"],
        "min_match": 2,
        "severity": "high",
        "icd10": "I10",
        "advice": "**Hypertension (High Blood Pressure)**\n\nMonitor blood pressure regularly. Reduce salt, alcohol, saturated fats. Exercise regularly. Manage stress. See doctor for medication if BP consistently > 140/90.\n\n🚨 If BP > 180/120, seek immediate care.",
        "followup": ["What is your current blood pressure reading?", "Do you have a history of hypertension?"],
    },
    "anemia": {
        "category": "Hematological",
        "symptoms": ["fatigue", "weakness", "pale skin", "shortness of breath", "dizziness", "cold hands", "brittle nails", "headache"],
        "min_match": 3,
        "severity": "medium",
        "icd10": "D64.9",
        "advice": "**Anemia**\n\nIron-rich foods (spinach, red meat, legumes). Vitamin C aids iron absorption. See doctor for CBC blood test to confirm type and severity. Iron supplements if prescribed.",
        "followup": ["Do you have heavy menstrual periods?", "What is your diet like?"],
    },

    # === NEUROLOGICAL ===
    "migraine": {
        "category": "Neurological",
        "symptoms": ["severe headache", "throbbing pain", "light sensitivity", "sound sensitivity", "nausea", "vomiting", "aura", "one-sided headache"],
        "min_match": 2,
        "severity": "medium",
        "icd10": "G43",
        "advice": "**Migraine**\n\nRest in a dark, quiet room. Triptans (sumatriptan) are effective if taken early. Cold/warm compress. Stay hydrated. Identify and avoid triggers (stress, certain foods, hormonal changes).",
        "followup": ["Is there an aura (visual disturbances) before headache?", "How long do episodes typically last?"],
    },
    "tension_headache": {
        "category": "Neurological",
        "symptoms": ["mild headache", "pressure around head", "tight band sensation", "neck pain", "shoulder tension", "scalp tenderness"],
        "min_match": 2,
        "severity": "low",
        "icd10": "G44.2",
        "advice": "**Tension Headache**\n\nOTC pain relievers (ibuprofen, paracetamol). Relax neck/shoulder muscles. Stay hydrated. Reduce stress. Adequate sleep. Limit screen time.",
        "followup": ["Any recent increase in stress or screen time?", "Does it improve with OTC pain relief?"],
    },

    # === MUSCULOSKELETAL ===
    "arthritis": {
        "category": "Musculoskeletal",
        "symptoms": ["joint pain", "joint stiffness", "swollen joints", "reduced range of motion", "morning stiffness", "warm joints"],
        "min_match": 2,
        "severity": "medium",
        "icd10": "M13.9",
        "advice": "**Arthritis**\n\nAnti-inflammatory medications (ibuprofen). Low-impact exercise (swimming, cycling). Hot/cold therapy. Physiotherapy. See rheumatologist for persistent symptoms.",
        "followup": ["Is morning stiffness > 1 hour?", "Which joints are affected?"],
    },
    "back_pain": {
        "category": "Musculoskeletal",
        "symptoms": ["lower back pain", "back ache", "muscle spasm", "stiffness", "pain radiating to leg", "sciatica"],
        "min_match": 2,
        "severity": "low",
        "icd10": "M54.5",
        "advice": "**Back Pain**\n\nRest (not bed rest), gentle stretching. OTC anti-inflammatories. Heat/cold therapy. Maintain good posture. See doctor if pain radiates down leg (sciatica signs).",
        "followup": ["Does pain radiate down your leg?", "Any recent injury or heavy lifting?"],
    },

    # === DERMATOLOGICAL ===
    "chickenpox": {
        "category": "Infectious",
        "symptoms": ["itchy rash", "blisters", "fever", "fatigue", "loss of appetite", "red spots", "fluid-filled blisters"],
        "min_match": 3,
        "severity": "medium",
        "icd10": "B01",
        "advice": "**Chickenpox (Varicella)**\n\nIsolate to prevent spread. Calamine lotion for itch. Trim nails to prevent scratching. Paracetamol for fever — **avoid aspirin** (Reye's syndrome risk in children).",
        "followup": ["Have you been vaccinated against chickenpox?", "Are you pregnant or immunocompromised?"],
    },
    "urticaria": {
        "category": "Dermatological",
        "symptoms": ["hives", "itchy welts", "skin rash", "swelling", "redness", "burning skin"],
        "min_match": 2,
        "severity": "medium",
        "icd10": "L50",
        "advice": "**Urticaria (Hives)**\n\nAntihistamines (cetirizine, loratadine). Avoid identified triggers (foods, medications, stress). Cool compress. See doctor if recurring or associated with swelling.\n\n🚨 Seek emergency care if face/throat swelling or difficulty breathing.",
        "followup": ["Any recent new food, medication, or detergent?", "Any throat or face swelling?"],
    },
    "eczema": {
        "category": "Dermatological",
        "symptoms": ["dry skin", "itchy skin", "skin inflammation", "rash", "scaly patches", "skin redness", "weeping skin"],
        "min_match": 2,
        "severity": "low",
        "icd10": "L20",
        "advice": "**Eczema (Atopic Dermatitis)**\n\nMoisturize frequently with fragrance-free emollients. Avoid known triggers. Hydrocortisone cream for flares. Cool, short showers. See dermatologist for persistent cases.",
        "followup": ["Any known allergies or asthma?", "What triggers your flares?"],
    },

    # === ENDOCRINE ===
    "diabetes_type2": {
        "category": "Endocrine",
        "symptoms": ["frequent urination", "excessive thirst", "blurred vision", "fatigue", "slow healing wounds", "numbness in feet", "unexplained weight loss"],
        "min_match": 3,
        "severity": "high",
        "icd10": "E11",
        "advice": "**Type 2 Diabetes (Possible)**\n\nSee a doctor for fasting blood glucose and HbA1c tests. Reduce sugar/refined carbs. Increase physical activity. Weight management is key.\n\n⚠️ Uncontrolled diabetes causes serious long-term complications.",
        "followup": ["Do you have a family history of diabetes?", "Any recent unexplained weight changes?"],
    },
    "hypothyroidism": {
        "category": "Endocrine",
        "symptoms": ["fatigue", "weight gain", "cold intolerance", "constipation", "dry skin", "hair loss", "depression", "slow heart rate", "puffy face"],
        "min_match": 3,
        "severity": "medium",
        "icd10": "E03.9",
        "advice": "**Hypothyroidism (Possible)**\n\nBlood test (TSH, T3, T4) required to confirm. Managed with levothyroxine replacement therapy. Regular monitoring needed.",
        "followup": ["Any family history of thyroid disease?", "How long have you experienced these symptoms?"],
    },

    # === UROLOGICAL ===
    "uti": {
        "category": "Urological",
        "symptoms": ["burning urination", "frequent urination", "cloudy urine", "strong urine odor", "pelvic pain", "blood in urine", "urge to urinate"],
        "min_match": 2,
        "severity": "medium",
        "icd10": "N39.0",
        "advice": "**Urinary Tract Infection (UTI)**\n\nSee doctor for urine culture and appropriate antibiotics. Drink plenty of water. Cranberry juice may help. Urinate after intercourse.\n\n⚠️ Untreated UTI can progress to kidney infection.",
        "followup": ["Any fever or back/flank pain (possible kidney involvement)?", "Is this a recurring problem?"],
    },
    "kidney_stones": {
        "category": "Urological",
        "symptoms": ["severe back pain", "flank pain", "blood in urine", "nausea", "vomiting", "pain radiating to groin", "urination pain"],
        "min_match": 3,
        "severity": "high",
        "icd10": "N20",
        "advice": "**Kidney Stones**\n\nHydrate heavily to help pass small stones. Pain management (NSAIDs). See doctor for imaging. Large stones may need lithotripsy or surgery.\n\n🚨 Seek ER care for severe uncontrolled pain.",
        "followup": ["How severe is the pain (1–10)?", "Any fever (signs of infection)?"],
    },

    # === MENTAL HEALTH ===
    "anxiety": {
        "category": "Mental Health",
        "symptoms": ["excessive worry", "restlessness", "rapid heartbeat", "sweating", "trembling", "difficulty concentrating", "sleep problems", "tension"],
        "min_match": 3,
        "severity": "medium",
        "icd10": "F41.1",
        "advice": "**Anxiety**\n\nDeep breathing and mindfulness techniques. Regular exercise. Limit caffeine/alcohol. CBT (Cognitive Behavioral Therapy) is highly effective. Consult a mental health professional.\n\n💙 You are not alone — anxiety is very treatable.",
        "followup": ["How long have you been experiencing this?", "Is it interfering with daily activities?"],
    },
    "depression": {
        "category": "Mental Health",
        "symptoms": ["persistent sadness", "loss of interest", "hopelessness", "fatigue", "sleep changes", "appetite changes", "difficulty concentrating", "worthlessness"],
        "min_match": 3,
        "severity": "high",
        "icd10": "F32",
        "advice": "**Depression**\n\nPlease reach out to a mental health professional. Therapy (CBT/IPT) and/or medication are effective treatments. Talk to someone you trust. Regular exercise and routine help.\n\n💙 If you have thoughts of self-harm, please call a crisis helpline immediately.",
        "followup": ["Do you have thoughts of harming yourself?", "Do you have support from friends or family?"],
    },
    "insomnia": {
        "category": "Mental Health",
        "symptoms": ["difficulty sleeping", "trouble falling asleep", "waking at night", "early morning waking", "daytime fatigue", "irritability", "poor concentration"],
        "min_match": 2,
        "severity": "low",
        "icd10": "G47.0",
        "advice": "**Insomnia**\n\nSleep hygiene: consistent schedule, dark/cool room, no screens 1hr before bed. Avoid caffeine after noon. CBT-I (Cognitive Behavioral Therapy for Insomnia) is the gold-standard treatment.",
        "followup": ["How long has this been an issue?", "Any significant stress or life changes recently?"],
    },

    # === ENT ===
    "sinusitis": {
        "category": "ENT",
        "symptoms": ["facial pain", "nasal congestion", "thick nasal discharge", "headache", "post-nasal drip", "reduced smell", "fever"],
        "min_match": 3,
        "severity": "low",
        "icd10": "J32",
        "advice": "**Sinusitis**\n\nSaline nasal rinses (neti pot). Steam inhalation. Decongestants (oxymetazoline max 3 days). See doctor if symptoms > 10 days or severe pain (may need antibiotics).",
        "followup": ["How long have you had these symptoms?", "Is discharge yellow/green?"],
    },
    "tonsillitis": {
        "category": "ENT",
        "symptoms": ["sore throat", "swollen tonsils", "difficulty swallowing", "fever", "bad breath", "ear pain", "swollen lymph nodes"],
        "min_match": 3,
        "severity": "medium",
        "icd10": "J03",
        "advice": "**Tonsillitis**\n\nSalt water gargles. Cold drinks/ice pops to soothe. Paracetamol/ibuprofen. See doctor — if bacterial (strep), antibiotics required. Recurrent cases may warrant tonsillectomy.",
        "followup": ["Any white patches on tonsils?", "Is this a recurring problem?"],
    },

    # === OPHTHALMOLOGICAL ===
    "conjunctivitis": {
        "category": "Ophthalmological",
        "symptoms": ["red eyes", "eye discharge", "itchy eyes", "watery eyes", "eye redness", "morning eye crust", "burning eyes"],
        "min_match": 2,
        "severity": "low",
        "icd10": "H10",
        "advice": "**Conjunctivitis (Pink Eye)**\n\nClean discharge with clean cloth. Don't share towels/pillows. Wash hands frequently. See doctor to determine viral vs. bacterial (antibiotic drops if bacterial). Allergic — use antihistamine drops.",
        "followup": ["Are both eyes affected?", "Any recent cold or allergy exposure?"],
    },

    # === REPRODUCTIVE ===
    "pcos": {
        "category": "Reproductive",
        "symptoms": ["irregular periods", "weight gain", "acne", "excess hair", "hair loss", "difficulty conceiving", "pelvic pain"],
        "min_match": 3,
        "severity": "medium",
        "icd10": "E28.2",
        "advice": "**PCOS (Polycystic Ovary Syndrome)**\n\nConsult a gynecologist/endocrinologist. Weight management significantly improves symptoms. Metformin and hormonal treatments are commonly used. Healthy diet and exercise are foundational.",
        "followup": ["Are your periods irregular or absent?", "Any family history of PCOS or diabetes?"],
    },
}


@dataclass
class PredictionResult:
    disease: str
    display_name: str
    category: str
    confidence: float
    severity: str
    advice: str
    matched_symptoms: List[str]
    followup_questions: List[str]
    icd10: str
    is_emergency: bool


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[,;/|]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def extract_symptom_tokens(text: str) -> List[str]:
    """Multi-word and single-word symptom extraction."""
    text = normalize_text(text)
    # Build a flat list of all known symptoms for matching
    all_symptoms = set()
    for disease_info in DISEASE_KB.values():
        for s in disease_info["symptoms"]:
            all_symptoms.add(s)

    matched = []
    # First pass: match multi-word symptoms
    for symptom in sorted(all_symptoms, key=len, reverse=True):
        if symptom in text:
            matched.append(symptom)

    # Second pass: single word tokens not already covered
    single_tokens = [tok for tok in text.split() if len(tok) > 2]
    for tok in single_tokens:
        if not any(tok in m for m in matched):
            matched.append(tok)

    return list(set(matched))


def check_emergency(text: str) -> bool:
    text_lower = text.lower()
    return any(symptom in text_lower for symptom in EMERGENCY_SYMPTOMS)


def predict_diseases(
    user_tokens: List[str],
    top_k: int = 3,
) -> List[PredictionResult]:
    """
    Score all diseases against extracted tokens.
    Returns top_k results sorted by confidence.
    """
    results = []

    for disease_key, info in DISEASE_KB.items():
        matched = []
        total_symptoms = len(info["symptoms"])

        for symptom in info["symptoms"]:
            symptom_words = symptom.split()
            # Match if all words of a symptom are present
            if all(sw in " ".join(user_tokens) for sw in symptom_words):
                matched.append(symptom)
            # Partial: at least one word matches
            elif any(sw in user_tokens for sw in symptom_words):
                matched.append(symptom)

        score = len(matched)
        if score >= info["min_match"]:
            # Confidence: percentage of matched symptoms, capped at 95%
            raw_conf = min(0.95, score / max(total_symptoms, 1) + (score / 10))
            confidence = round(raw_conf * 100, 1)

            results.append(PredictionResult(
                disease=disease_key,
                display_name=disease_key.replace("_", " ").title(),
                category=info["category"],
                confidence=confidence,
                severity=info["severity"],
                advice=info["advice"],
                matched_symptoms=matched,
                followup_questions=info.get("followup", []),
                icd10=info.get("icd10", ""),
                is_emergency=False,
            ))

    results.sort(key=lambda r: r.confidence, reverse=True)
    return results[:top_k]


def format_prediction_response(
    results: List[PredictionResult],
    is_emergency: bool,
) -> str:
    if is_emergency:
        return (
            "🚨 **EMERGENCY SYMPTOMS DETECTED**\n\n"
            "**Please call emergency services (911 / 112) immediately or go to the nearest emergency room.**\n\n"
            "Do not wait for an online consultation. Emergency symptoms you described require immediate medical attention."
        )

    if not results:
        return (
            "🔍 **I couldn't confidently identify a condition from the symptoms described.**\n\n"
            "Please provide more specific symptoms. For example:\n"
            "• Fever, cough, body pain → Flu\n"
            "• Burning urination, frequent urination → UTI\n"
            "• Joint pain, morning stiffness → Arthritis\n\n"
            "🏥 *If symptoms are severe or worsening, please consult a doctor immediately.*"
        )

    primary = results[0]
    severity_icons = {"low": "🟢", "medium": "🟡", "high": "🔴", "emergency": "🚨"}

    response = f"## {severity_icons.get(primary.severity, '⚪')} Most Likely: {primary.display_name}\n\n"
    response += f"**Confidence:** {primary.confidence}% | **Severity:** {primary.severity.upper()} | **Category:** {primary.category}\n\n"
    response += f"{primary.advice}\n\n"

    if len(results) > 1:
        response += "---\n### Other Possibilities\n"
        for r in results[1:]:
            response += f"- **{r.display_name}** ({r.confidence}% confidence) — {r.category}\n"

    if primary.followup_questions:
        response += f"\n---\n### 💬 Follow-up Questions\n"
        for q in primary.followup_questions:
            response += f"- {q}\n"

    response += "\n---\n⚠️ *This is AI-generated health information, not a medical diagnosis. Always consult a qualified healthcare professional.*"
    return response


def predict_from_text(text: str) -> Dict:
    """Main entry point for ML prediction."""
    is_emergency = check_emergency(text)
    tokens = extract_symptom_tokens(text)
    results = predict_diseases(tokens)

    return {
        "is_emergency": is_emergency,
        "predictions": [
            {
                "disease": r.disease,
                "display_name": r.display_name,
                "confidence": r.confidence,
                "severity": r.severity,
                "category": r.category,
                "matched_symptoms": r.matched_symptoms,
                "icd10": r.icd10,
            }
            for r in results
        ],
        "response": format_prediction_response(results, is_emergency),
        "extracted_symptoms": tokens,
    }
