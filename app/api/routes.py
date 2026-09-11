from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.schemas.question import (
    CognitiveLevel,
    DifficultyLevel,
    MixedQuestionRequest,
    QuestionRequest,
    QuestionResponse,
    QuestionType,
)
from app.services.ai_service import generate_questions
from app.services.pdf_service import extract_text_from_pdf

router = APIRouter(prefix="/questions", tags=["Question Generation"])


@router.post(
    "/generate",
    response_model=QuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Questions from Text",
    description="Accepts educational material text and generates structured questions (MCQ, Short Answer, or True/False) with answers and explanations."
)
async def generate_from_text(request: QuestionRequest):
    """
    Generate questions from educational text input.
    """
    ai_result = await generate_questions(
        content=request.text,
        number_of_questions=request.number_of_questions,
        question_type=request.question_type.value,
        difficulty=request.difficulty.value,
        cognitive_level=request.cognitive_level.value if request.cognitive_level else None,
    )

    questions = ai_result["questions"]

    return QuestionResponse(
        success=True,
        total_questions=len(questions),
        source_type="text",
        questions=questions,
        metadata={
            "requested_count": request.number_of_questions,
            "question_type": request.question_type.value,
            "difficulty": request.difficulty.value,
            "cognitive_level": request.cognitive_level.value if request.cognitive_level else None,
            "material_length": len(request.text),
            "ai_provider": ai_result.get("provider", "default"),
        }
    )


@router.post(
    "/generate-from-pdf",
    response_model=QuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Questions from PDF File",
    description="Upload a PDF file (up to 5MB) containing study notes, textbook chapters, or educational material to generate assessment questions."
)
async def generate_from_pdf(
    file: UploadFile = File(..., description="PDF document containing educational material (max 5MB)"),
    number_of_questions: int = Form(5, ge=1, le=50, description="Total questions to generate (1-50)"),
    question_type: QuestionType = Form(QuestionType.MCQ, description="Type: 'mcq', 'short_answer', or 'true_false'"),
    difficulty: DifficultyLevel = Form(DifficultyLevel.MEDIUM, description="Difficulty: 'easy', 'medium', or 'hard'"),
    cognitive_level: Optional[CognitiveLevel] = Form(None, description="Optional Bloom's Taxonomy cognitive level")
):
    """
    Extract text from an uploaded PDF and generate questions using Generative AI.
    """
    # Extract text from PDF
    extracted_text = await extract_text_from_pdf(file)

    ai_result = await generate_questions(
        content=extracted_text,
        number_of_questions=number_of_questions,
        question_type=question_type.value,
        difficulty=difficulty.value,
        cognitive_level=cognitive_level.value if cognitive_level else None,
    )

    questions = ai_result["questions"]

    return QuestionResponse(
        success=True,
        total_questions=len(questions),
        source_type="pdf",
        questions=questions,
        metadata={
            "filename": file.filename,
            "requested_count": number_of_questions,
            "question_type": question_type.value,
            "difficulty": difficulty.value,
            "cognitive_level": cognitive_level.value if cognitive_level else None,
            "extracted_text_length": len(extracted_text),
            "ai_provider": ai_result.get("provider", "default"),
        }
    )


@router.post(
    "/mixed",
    response_model=QuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Mixed Question Types",
    description="Generates an assessment quiz containing a diverse mix of MCQ, Short Answer, and True/False questions."
)
async def generate_mixed_questions(request: MixedQuestionRequest):
    """
    Generate an assessment containing a mixture of MCQ, Short Answer, and True/False questions.
    """
    ai_result = await generate_questions(
        content=request.text,
        number_of_questions=request.number_of_questions,
        question_type="mixed",
        difficulty=request.difficulty.value,
        cognitive_level=request.cognitive_level.value if request.cognitive_level else None,
    )

    questions = ai_result["questions"]

    return QuestionResponse(
        success=True,
        total_questions=len(questions),
        source_type="text",
        questions=questions,
        metadata={
            "requested_count": request.number_of_questions,
            "question_type": "mixed",
            "difficulty": request.difficulty.value,
            "cognitive_level": request.cognitive_level.value if request.cognitive_level else None,
            "material_length": len(request.text),
            "ai_provider": ai_result.get("provider", "default"),
        }
    )
