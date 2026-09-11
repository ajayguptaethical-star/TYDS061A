import json
import logging
import re
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from app.config import settings
from app.schemas.question import GeneratedQuestion
from app.utils.prompts import build_question_prompt

logger = logging.getLogger("eduquestion.ai_service")


def extract_json_from_llm_response(raw_text: str) -> Any:
    """
    Cleans and extracts JSON content from an LLM response string,
    safely handling markdown code fences.
    """
    cleaned = raw_text.strip()
    
    # Remove markdown code block fences if present (```json ... ``` or ``` ... ```)
    if cleaned.startswith("```"):
        # Match ```json or ``` at beginning and ``` at end
        pattern = r"^```(?:json)?\s*([\s\S]*?)\s*```$"
        match = re.search(pattern, cleaned)
        if match:
            cleaned = match.group(1).strip()

    # Sometimes models include text before or after the array
    json_start = cleaned.find("[")
    json_end = cleaned.rfind("]")
    if json_start != -1 and json_end != -1 and json_end > json_start:
        cleaned = cleaned[json_start : json_end + 1]

    return json.loads(cleaned)


def _generate_rule_based_fallback_questions(
    content: str,
    number_of_questions: int,
    question_type: str,
    difficulty: str,
    cognitive_level: Optional[str] = None
) -> List[GeneratedQuestion]:
    """
    Heuristic rule-based fallback generator used when no external AI API key is configured
    or when external AI services are unreachable during offline local development.
    """
    sentences = [s.strip() for s in re.split(r"[.!?]+", content) if len(s.strip()) > 20]
    if not sentences:
        sentences = [content[:120].strip()]

    questions: List[GeneratedQuestion] = []
    total = min(number_of_questions, max(1, len(sentences)))

    for idx in range(total):
        target_sentence = sentences[idx % len(sentences)]
        words = [w for w in re.findall(r"\b[A-Za-z]{4,}\b", target_sentence)]
        key_term = words[0] if words else "Educational Concept"
        q_id = idx + 1
        
        # Determine specific question type for mixed or specific requests
        cur_type = question_type
        if question_type == "mixed":
            types_cycle = ["mcq", "short_answer", "true_false"]
            cur_type = types_cycle[idx % len(types_cycle)]

        if cur_type == "mcq":
            options = [
                f"{key_term} (Primary subject from the text)",
                f"Alternative unrelated concept {idx + 1}",
                f"Inverted hypothesis regarding {key_term.lower()}",
                "None of the provided options"
            ]
            questions.append(
                GeneratedQuestion(
                    id=q_id,
                    question=f"Based on the text, what key statement applies to '{key_term}'?",
                    type="mcq",
                    difficulty=difficulty,
                    options=options,
                    answer=options[0],
                    explanation=f"Referenced from study material: \"{target_sentence}\"",
                    cognitive_level=cognitive_level or "understand"
                )
            )
        elif cur_type == "true_false":
            questions.append(
                GeneratedQuestion(
                    id=q_id,
                    question=f"True or False: According to the material, {target_sentence}.",
                    type="true_false",
                    difficulty=difficulty,
                    options=["True", "False"],
                    answer="True",
                    explanation=f"Directly verified by the source text statement: \"{target_sentence}\"",
                    cognitive_level=cognitive_level or "remember"
                )
            )
        else:  # short_answer
            questions.append(
                GeneratedQuestion(
                    id=q_id,
                    question=f"Summarize what the material states regarding {key_term}.",
                    type="short_answer",
                    difficulty=difficulty,
                    options=None,
                    answer=target_sentence,
                    explanation=f"Direct factual excerpt: \"{target_sentence}\"",
                    cognitive_level=cognitive_level or "understand"
                )
            )

    return questions


async def generate_questions_with_gemini(prompt: str) -> str:
    """
    Calls Google Gemini Generative AI API using the google.generativeai SDK.
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="google-generativeai package is not installed."
        )

    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    # Try preferred flash model, fallback to gemini-pro if needed
    model_name = settings.GEMINI_MODEL
    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={"response_mime_type": "application/json"}
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as exc:
        logger.warning(f"Error calling {model_name}: {exc}. Trying fallback model gemini-1.5-pro...")
        try:
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config={"response_mime_type": "application/json"}
            )
            response = model.generate_content(prompt)
            return response.text
        except Exception as inner_exc:
            logger.error(f"Gemini generation error: {inner_exc}")
            raise HTTPException(
                status_code=503,
                detail="Question generation service temporarily unavailable"
            )


async def generate_questions_with_openai(prompt: str) -> str:
    """
    Calls OpenAI ChatCompletion API.
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="openai package is not installed."
        )

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    try:
        completion = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful educational question generator that returns raw JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return completion.choices[0].message.content or ""
    except Exception as exc:
        logger.error(f"OpenAI generation error: {exc}")
        raise HTTPException(
            status_code=503,
            detail="Question generation service temporarily unavailable"
        )


async def generate_questions(
    content: str,
    number_of_questions: int,
    question_type: str,
    difficulty: str,
    cognitive_level: Optional[str] = None
) -> Dict[str, Any]:
    """
    Coordinates question generation across AI providers, validates output structure,
    and returns a clean list of GeneratedQuestion objects.
    """
    prompt = build_question_prompt(
        content=content,
        number_of_questions=number_of_questions,
        question_type=question_type,
        difficulty=difficulty,
        cognitive_level=cognitive_level
    )

    provider_used = "heuristic_fallback"
    raw_response_text = ""

    # Check which provider to call
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            raw_response_text = await generate_questions_with_gemini(prompt)
            provider_used = f"gemini ({settings.GEMINI_MODEL})"
        except HTTPException:
            # Re-raise standard HTTPExceptions if it was a strict error
            raise
    elif settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
        try:
            raw_response_text = await generate_questions_with_openai(prompt)
            provider_used = f"openai ({settings.OPENAI_MODEL})"
        except HTTPException:
            raise
    else:
        # If neither API key is provided, use high-quality heuristic fallback
        logger.info("No AI API key found. Using educational heuristic engine.")
        generated_list = _generate_rule_based_fallback_questions(
            content=content,
            number_of_questions=number_of_questions,
            question_type=question_type,
            difficulty=difficulty,
            cognitive_level=cognitive_level
        )
        return {
            "questions": generated_list,
            "provider": "educational_fallback_generator (Provide GEMINI_API_KEY in .env for full LLM generation)",
        }

    # Parse JSON from AI response
    try:
        parsed_data = extract_json_from_llm_response(raw_response_text)
        
        # In case the model returned a dict wrapping {"questions": [...]}
        if isinstance(parsed_data, dict):
            if "questions" in parsed_data:
                parsed_data = parsed_data["questions"]
            else:
                # First list value found in dict
                list_vals = [v for v in parsed_data.values() if isinstance(v, list)]
                if list_vals:
                    parsed_data = list_vals[0]
                else:
                    parsed_data = [parsed_data]

        if not isinstance(parsed_data, list):
            raise ValueError("Expected JSON array of question objects")

        validated_questions: List[GeneratedQuestion] = []
        for index, item in enumerate(parsed_data):
            q_id = item.get("id") or (index + 1)
            q_text = item.get("question") or "Question text missing"
            q_type = item.get("type") or question_type
            q_diff = item.get("difficulty") or difficulty
            q_opts = item.get("options")
            q_ans = str(item.get("answer") or "")
            q_expl = item.get("explanation") or "Derived from provided educational content."
            q_cog = item.get("cognitive_level") or cognitive_level

            # If MCQ, ensure options exist
            if q_type == "mcq" and (not q_opts or not isinstance(q_opts, list)):
                q_opts = [q_ans, "Option B", "Option C", "Option D"]

            validated_questions.append(
                GeneratedQuestion(
                    id=int(q_id),
                    question=str(q_text),
                    type=str(q_type),
                    difficulty=str(q_diff),
                    options=q_opts if isinstance(q_opts, list) else None,
                    answer=q_ans,
                    explanation=q_expl,
                    cognitive_level=q_cog
                )
            )

        return {
            "questions": validated_questions[:number_of_questions],
            "provider": provider_used,
        }

    except Exception as parse_exc:
        logger.error(f"Failed to parse AI response into Question schema: {parse_exc}. Raw: {raw_response_text[:300]}")
        # Fallback gracefully so the user request does not break
        fallback_list = _generate_rule_based_fallback_questions(
            content=content,
            number_of_questions=number_of_questions,
            question_type=question_type,
            difficulty=difficulty,
            cognitive_level=cognitive_level
        )
        return {
            "questions": fallback_list,
            "provider": f"{provider_used} (fallback parsed)",
        }
