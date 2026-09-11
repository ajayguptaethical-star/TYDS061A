import io
import re
from fastapi import HTTPException, UploadFile
import pypdf
from app.config import settings


def clean_extracted_text(raw_text: str) -> str:
    """
    Cleans up raw extracted text by normalizing whitespace and removing non-printable characters.
    """
    if not raw_text:
        return ""
    # Remove null bytes
    cleaned = raw_text.replace("\x00", "")
    # Normalize multiple newlines and spaces
    cleaned = re.sub(r"\r\n|\r", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned.strip()


async def extract_text_from_pdf(file: UploadFile) -> str:
    """
    Validates uploaded PDF file and extracts text using pypdf.
    Raises HTTPException for invalid file type, file size exceeding limit, or failure to extract text.
    """
    # 1. Validate file extension
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are supported."
        )

    # 2. Read file bytes and check size limit (5MB)
    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read uploaded file: {str(exc)}"
        )
    finally:
        await file.seek(0)

    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF file is empty."
        )

    if len(content) > settings.MAX_PDF_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"PDF size exceeds the maximum limit of {settings.MAX_PDF_SIZE_MB}MB."
        )

    # 3. Extract text from PDF pages
    extracted_pages = []
    try:
        pdf_stream = io.BytesIO(content)
        reader = pypdf.PdfReader(pdf_stream)
        
        if len(reader.pages) == 0:
            raise HTTPException(
                status_code=400,
                detail="Unable to extract text from PDF: PDF contains no pages."
            )

        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                extracted_pages.append(page_text)
                
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to extract text from PDF: {str(exc)}"
        )

    full_text = "\n\n".join(extracted_pages)
    cleaned_text = clean_extracted_text(full_text)

    if not cleaned_text or len(cleaned_text) < 10:
        raise HTTPException(
            status_code=400,
            detail="Unable to extract text from PDF. The document may be empty or contain only non-text images."
        )

    return cleaned_text
