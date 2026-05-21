"""
MediBot AI — OCR & Document Analysis API
Prescription OCR, PDF report analysis, medical image processing
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import Optional
import logging
import os
import uuid

from core.auth import get_current_user
from core.ai_engine import ai_engine

router = APIRouter()
logger = logging.getLogger("medibot.ocr")

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_DOC_TYPES = {"application/pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/prescription")
async def analyze_prescription(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """
    Upload a prescription image for OCR and AI analysis.
    Extracts medication names, dosages, and instructions.
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WEBP images allowed")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    # Save temp file
    tmp_path = f"/tmp/ocr_{uuid.uuid4()}.jpg"
    try:
        with open(tmp_path, "wb") as f:
            f.write(content)

        extracted_text = _run_ocr(tmp_path)

        if not extracted_text.strip():
            return {
                "success": False,
                "message": "Could not extract text from the image. Please ensure the image is clear.",
                "extracted_text": "",
                "analysis": None,
            }

        # AI analysis of extracted text
        analysis = await ai_engine.chat(
            messages=[{
                "role": "user",
                "content": (
                    f"Analyze this medical prescription text and extract:\n"
                    f"1. Medication names and dosages\n"
                    f"2. Frequency and duration of doses\n"
                    f"3. Important instructions or warnings\n"
                    f"4. Any drug interactions to be aware of\n\n"
                    f"Prescription text:\n{extracted_text}"
                ),
            }],
            temperature=0.1,
        )

        return {
            "success": True,
            "extracted_text": extracted_text,
            "analysis": analysis["reply"],
            "file_name": file.filename,
        }

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/report")
async def analyze_medical_report(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """
    Upload a PDF medical report for AI analysis.
    Provides plain-language explanation of test results.
    """
    if file.content_type not in ALLOWED_DOC_TYPES | ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF and image files allowed")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    import os
    import tempfile

    tmp_dir = tempfile.gettempdir()
    tmp_path = os.path.join(tmp_dir, f"report_{uuid.uuid4()}.pdf")
    try:
        with open(tmp_path, "wb") as f:
            f.write(content)

        if file.content_type == "application/pdf":
            extracted_text = _extract_pdf_text(tmp_path)
        else:
            extracted_text = _run_ocr(tmp_path)

        if not extracted_text.strip():
            return {
                "success": False,
                "message": "Could not extract text from the document.",
                "extracted_text": "",
                "analysis": None,
            }

        analysis = await ai_engine.chat(
            messages=[{
                "role": "user",
                "content": (
                    f"Analyze this medical report and explain in simple language:\n"
                    f"1. What tests were performed\n"
                    f"2. What the results mean\n"
                    f"3. Which values are normal vs abnormal\n"
                    f"4. What the patient should discuss with their doctor\n"
                    f"5. Any urgent findings that need immediate attention\n\n"
                    f"Report text:\n{extracted_text[:3000]}"
                ),
            }],
            temperature=0.1,
        )

        return {
            "success": True,
            "extracted_text": extracted_text[:2000],
            "analysis": analysis["reply"],
            "file_name": file.filename,
        }

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def _run_ocr(image_path: str) -> str:
    """Run Tesseract OCR on an image file."""
    try:
        import pytesseract
        from PIL import Image
        from core.config import settings
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        img = Image.open(image_path)
        return pytesseract.image_to_string(img, config="--psm 6")
    except ImportError:
        logger.warning("pytesseract/PIL not installed — OCR unavailable")
        return "[OCR not available — install pytesseract and Pillow]"
    except Exception as e:
        logger.error(f"OCR error: {e}")
        return ""


def _extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        logger.warning("pypdf not installed")
        return "[PDF extraction not available — install pypdf]"
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return ""
