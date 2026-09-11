from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class QuestionType(str, Enum):
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    TRUE_FALSE = "true_false"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class CognitiveLevel(str, Enum):
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class QuestionRequest(BaseModel):
    text: str = Field(
        ...,
        description="Educational material, notes, chapter content, or study text",
        examples=["Photosynthesis is the process by which green plants convert sunlight, water, and carbon dioxide into glucose and oxygen."]
    )
    number_of_questions: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of questions to generate (between 1 and 50)",
        examples=[5]
    )
    question_type: QuestionType = Field(
        default=QuestionType.MCQ,
        description="Type of questions: 'mcq', 'short_answer', or 'true_false'",
        examples=["mcq"]
    )
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.MEDIUM,
        description="Difficulty level: 'easy', 'medium', or 'hard'",
        examples=["medium"]
    )
    cognitive_level: Optional[CognitiveLevel] = Field(
        default=None,
        description="Optional Bloom's Taxonomy cognitive level (e.g. 'remember', 'understand', 'apply')",
        examples=["understand"]
    )

    @field_validator("text")
    @classmethod
    def validate_non_empty_text(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Educational material cannot be empty")
        if len(cleaned) < 10:
            raise ValueError("Educational material is too short. Please provide at least 10 characters.")
        return cleaned


class MixedQuestionRequest(BaseModel):
    text: str = Field(
        ...,
        description="Educational material text to generate mixed-style questions from",
        examples=["Artificial intelligence (AI) is the simulation of human intelligence in machines programmed to think and learn."]
    )
    number_of_questions: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Total number of mixed questions to generate (between 1 and 50)",
        examples=[6]
    )
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.MEDIUM,
        description="Difficulty level: 'easy', 'medium', or 'hard'",
        examples=["medium"]
    )
    cognitive_level: Optional[CognitiveLevel] = Field(
        default=None,
        description="Optional Bloom's Taxonomy level",
        examples=["understand"]
    )

    @field_validator("text")
    @classmethod
    def validate_non_empty_text(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Educational material cannot be empty")
        if len(cleaned) < 10:
            raise ValueError("Educational material is too short. Please provide at least 10 characters.")
        return cleaned


class GeneratedQuestion(BaseModel):
    id: int = Field(..., description="Sequential question identifier")
    question: str = Field(..., description="The generated question text")
    type: str = Field(..., description="Type of question: mcq, short_answer, or true_false")
    difficulty: str = Field(..., description="Difficulty level: easy, medium, or hard")
    options: Optional[List[str]] = Field(
        default=None,
        description="List of 4 multiple-choice options (only for MCQ questions)"
    )
    answer: str = Field(..., description="Correct answer text")
    explanation: Optional[str] = Field(
        default=None,
        description="Explanation referencing the material for why the answer is correct"
    )
    cognitive_level: Optional[str] = Field(
        default=None,
        description="Associated Bloom's taxonomy cognitive level if requested"
    )


class QuestionResponse(BaseModel):
    success: bool = Field(default=True, description="Indicates if question generation succeeded")
    total_questions: int = Field(..., description="Total count of questions returned")
    source_type: str = Field(default="text", description="Source of input ('text' or 'pdf')")
    questions: List[GeneratedQuestion] = Field(..., description="List of generated questions")
    metadata: Optional[dict] = Field(
        default=None,
        description="Additional execution metadata, e.g. material length, provider"
    )


class HealthResponse(BaseModel):
    message: str = "EduQuestion AI API is running"
    status: str = "healthy"
    version: str = "1.0.0"
