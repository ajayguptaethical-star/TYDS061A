from typing import Optional


def build_question_prompt(
    content: str,
    number_of_questions: int,
    question_type: str,
    difficulty: str,
    cognitive_level: Optional[str] = None
) -> str:
    """
    Constructs a structured prompt forcing the AI to return a strictly valid JSON array.
    """
    type_instructions = ""
    if question_type == "mcq":
        type_instructions = (
            "- Generate Multiple Choice Questions (MCQ).\n"
            "- Each question MUST have exactly 4 plausible options in an array (e.g. ['Option A', 'Option B', 'Option C', 'Option D']).\n"
            "- The 'answer' field MUST exactly match one of the items in the 'options' array.\n"
            "- Set 'type' to 'mcq'."
        )
    elif question_type == "short_answer":
        type_instructions = (
            "- Generate Short Answer Questions.\n"
            "- 'options' field should be null.\n"
            "- 'answer' should be a concise, direct, factual answer based directly on the material.\n"
            "- Set 'type' to 'short_answer'."
        )
    elif question_type == "true_false":
        type_instructions = (
            "- Generate True/False Questions.\n"
            "- The 'question' should be a declarative statement that can be evaluated as True or False based on the text.\n"
            "- 'options' should be ['True', 'False'].\n"
            "- 'answer' MUST be either 'True' or 'False'.\n"
            "- Set 'type' to 'true_false'."
        )
    elif question_type == "mixed":
        type_instructions = (
            "- Generate a balanced mix of 'mcq', 'short_answer', and 'true_false' questions.\n"
            "- For 'mcq', include 4 options.\n"
            "- For 'true_false', include options ['True', 'False'] and answer 'True' or 'False'.\n"
            "- For 'short_answer', set 'options' to null.\n"
            "- Set 'type' appropriately for each question."
        )

    cognitive_instruction = ""
    if cognitive_level:
        cognitive_instruction = f"- Target Bloom's Taxonomy Cognitive Level: {cognitive_level.upper()} (e.g. remember, understand, apply, analyze, evaluate, create)."

    prompt = f"""You are an expert educational assessment specialist and question generator.

Task:
Generate {number_of_questions} high-quality questions based EXCLUSIVELY on the provided Educational Material.

Parameters:
- Target Count: {number_of_questions}
- Question Type: {question_type}
- Difficulty Level: {difficulty} (Easy = basic factual recall; Medium = conceptual understanding; Hard = analytical and synthesis questions)
{cognitive_instruction}

Type-specific Guidelines:
{type_instructions}

Strict Rules:
1. Ground truth: Use ONLY information explicitly stated or directly inferred from the educational material. Do not hallucinate or add outside knowledge.
2. For each question, provide an 'explanation' field quoting or referencing the material explaining why the answer is correct.
3. Your response MUST BE A VALID RAW JSON ARRAY of objects, with no markdown code fences, no extra preamble, and no conversational text.

Required JSON Schema for each object in the array:
{{
  "id": 1,
  "question": "string",
  "type": "{question_type}",
  "difficulty": "{difficulty}",
  "options": ["string", "string", "string", "string"] or null,
  "answer": "string",
  "explanation": "string",
  "cognitive_level": "{cognitive_level or difficulty}"
}}

Educational Material:
\"\"\"
{content}
\"\"\"
"""
    return prompt.strip()
