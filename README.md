# 🎓 EduQuestion AI

> **REST API for Automatic Question Generation from Educational Materials using Generative AI (Google Gemini / OpenAI)**

EduQuestion AI is a high-performance FastAPI REST API that takes educational materials—such as raw study notes, textbook chapters, or uploaded PDF documents—and automatically generates high-quality assessment questions (Multiple Choice Questions, Short Answer, True/False, or Mixed) along with correct answers, distractor options, and evidence-grounded explanations.

---

## 🌟 Key Features

- **Multiple Input Formats**: Directly provide educational text or upload PDF documents (up to 5MB).
- **Multiple Assessment Types**:
  - **MCQ (Multiple Choice)**: 4 plausible options, 1 verified correct answer, and explanation.
  - **Short Answer**: Direct questions requiring concise, factual answers.
  - **True / False**: Declarative evaluation questions grounded in the source text.
  - **Mixed Mode**: Balanced assessment combining multiple question styles.
- **Adjustable Difficulty**: `easy` (factual recall), `medium` (conceptual understanding), and `hard` (analytical/synthesis).
- **Bloom's Taxonomy Support** *(Optional)*: Target specific cognitive levels (`remember`, `understand`, `apply`, `analyze`, `evaluate`, `create`).
- **Strict Ground Truth Prompting**: Prevents hallucinations by constraining generation strictly to the provided source text.
- **Interactive Web Playground**: Built-in visual testing tool at `/demo` to easily test text and PDF uploads without needing an external frontend.
- **Automatic Swagger & ReDoc**: Complete interactive API documentation at `/docs` and `/redoc`.
- **Offline Fallback Engine**: Works smoothly out of the box even before configuring an API key.

---

## 🏗️ System Architecture

```text
                    ┌─────────────────────────┐
                    │  Client / Web / Mobile  │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      FastAPI App        │
                    │   (/api/v1/questions)   │
                    └────────────┬────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
        ┌──────────────────┐            ┌──────────────────┐
        │    Text Input    │            │    PDF Upload    │
        └────────┬─────────┘            └────────┬─────────┘
                 │                               │
                 │                               ▼
                 │                      ┌──────────────────┐
                 │                      │   pypdf Text     │
                 │                      │   Extraction     │
                 │                      └────────┬─────────┘
                 │                               │
                 └───────────────┬───────────────┘
                                 ▼
                        ┌──────────────────┐
                        │  Text Sanitizer  │
                        └────────┬─────────┘
                                 ▼
                        ┌──────────────────┐
                        │  Prompt Builder  │
                        └────────┬─────────┘
                                 ▼
                        ┌──────────────────┐
                        │  Generative AI   │
                        │ (Gemini/OpenAI)  │
                        └────────┬─────────┘
                                 ▼
                        ┌──────────────────┐
                        │ JSON Validation  │
                        │  (Pydantic v2)   │
                        └────────┬─────────┘
                                 ▼
                        ┌──────────────────┐
                        │   API Response   │
                        └──────────────────┘
```

---

## 📁 Project Structure

```text
eduquestion-ai/
│
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app instance, CORS, routes & demo UI
│   ├── config.py            # Environment settings & limits
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # /generate, /generate-from-pdf, /mixed endpoints
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── question.py      # Pydantic v2 validation models & schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py    # Gemini & OpenAI Generative AI integrations
│   │   └── pdf_service.py   # PDF file validation and text extraction
│   └── utils/
│       ├── __init__.py
│       └── prompts.py       # Prompt engineering & strict JSON template
│
├── uploads/                 # Temporary storage (if needed)
├── tests/
│   ├── __init__.py
│   ├── test_questions.py    # Test cases for text generation & validation
│   └── test_pdf.py          # Test cases for PDF processing & size limits
│
├── .env                     # Local environment variables
├── .env.example             # Example environment variables
├── .gitignore               # Git ignored patterns
├── requirements.txt         # Project dependencies
├── README.md                # Documentation
└── run.py                   # Server startup entrypoint
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.12)
- pip

### 2. Setup Environment

```bash
# Clone or navigate to the directory
cd Ajay

# Install required dependencies
pip install -r requirements.txt
```

### 3. Configure API Key (Optional for LLM)
Copy `.env.example` to `.env` and paste your Google Gemini API Key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-1.5-flash
MAX_PDF_SIZE_MB=5
```
> *Note: If no API key is provided, EduQuestion AI automatically activates its internal educational heuristic engine so all endpoints can still be tested immediately!*

### 4. Run the Server

```bash
python run.py
```
or via Uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will now be live:
- 🌐 **Interactive Demo**: [http://localhost:8000/demo](http://localhost:8000/demo)
- 📚 **Swagger UI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- 📖 **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- 💓 **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 📡 API Endpoints

### 1. Health Check
`GET /` or `GET /health`

**Response:**
```json
{
  "message": "EduQuestion AI API is running",
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### 2. Generate Questions from Text
`POST /api/v1/questions/generate`

**Request Body:**
```json
{
  "text": "Photosynthesis is the process by which green plants convert sunlight into chemical energy stored in glucose. During this process, plants absorb water and carbon dioxide, releasing oxygen into the atmosphere.",
  "number_of_questions": 3,
  "question_type": "mcq",
  "difficulty": "medium",
  "cognitive_level": "understand"
}
```

**Response:**
```json
{
  "success": true,
  "total_questions": 3,
  "source_type": "text",
  "questions": [
    {
      "id": 1,
      "question": "What gas is released into the atmosphere during photosynthesis?",
      "type": "mcq",
      "difficulty": "medium",
      "options": [
        "Carbon dioxide",
        "Oxygen",
        "Nitrogen",
        "Hydrogen"
      ],
      "answer": "Oxygen",
      "explanation": "The text states that plants release oxygen into the atmosphere during photosynthesis.",
      "cognitive_level": "understand"
    }
  ],
  "metadata": {
    "requested_count": 3,
    "question_type": "mcq",
    "difficulty": "medium",
    "cognitive_level": "understand",
    "material_length": 218,
    "ai_provider": "gemini (gemini-1.5-flash)"
  }
}
```

---

### 3. Generate Questions from PDF
`POST /api/v1/questions/generate-from-pdf`

**Content-Type:** `multipart/form-data`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file` | Binary File | Yes | - | PDF document (max 5MB) |
| `number_of_questions` | Integer | No | `5` | Between 1 and 50 |
| `question_type` | String | No | `mcq` | `mcq`, `short_answer`, `true_false` |
| `difficulty` | String | No | `medium` | `easy`, `medium`, `hard` |
| `cognitive_level` | String | No | `null` | Bloom's taxonomy level |

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/questions/generate-from-pdf" \
  -F "file=@notes.pdf" \
  -F "number_of_questions=5" \
  -F "question_type=mcq" \
  -F "difficulty=medium"
```

---

### 4. Generate Mixed Questions
`POST /api/v1/questions/mixed`

**Request Body:**
```json
{
  "text": "Artificial Intelligence is the simulation of human intelligence in machines. Machine learning is a subset of AI that allows systems to learn from data without explicit programming.",
  "number_of_questions": 3,
  "difficulty": "medium"
}
```

**Response:**
Generates a quiz containing a balanced mix of MCQ, Short Answer, and True/False questions.

---

## 🛡️ Input Validation & Error Handling

All inputs are validated using Pydantic v2 models:

| Scenario | HTTP Status | Response |
|----------|-------------|----------|
| Empty text | `422` | `{"detail": "Educational material cannot be empty"}` |
| Questions < 1 or > 50 | `422` | `{"detail": "Number of questions must be between 1 and 50"}` |
| Invalid Question Type | `422` | `{"detail": "Invalid question type..."}` |
| Non-PDF file upload | `400` | `{"detail": "Invalid file type. Only PDF files are supported."}` |
| PDF > 5MB | `400` | `{"detail": "PDF size exceeds the maximum limit of 5MB."}` |
| Unreadable/Empty PDF | `400` | `{"detail": "Unable to extract text from PDF..."}` |
| AI API Outage | `503` | `{"detail": "Question generation service temporarily unavailable"}` |

---

## 🧪 Running Automated Tests

Run the complete test suite with `pytest`:

```bash
pytest -v
```

Output:
```text
tests/test_pdf.py::test_clean_extracted_text_helper PASSED               [  7%]
tests/test_pdf.py::test_invalid_file_extension PASSED                    [ 14%]
tests/test_pdf.py::test_empty_pdf_rejection PASSED                       [ 21%]
tests/test_questions.py::test_root_health_check PASSED                   [ 28%]
tests/test_questions.py::test_health_endpoint PASSED                     [ 35%]
tests/test_questions.py::test_generate_mcq_success PASSED                [ 42%]
tests/test_questions.py::test_generate_short_answer_success PASSED       [ 50%]
tests/test_questions.py::test_generate_true_false_success PASSED         [ 57%]
tests/test_questions.py::test_generate_mixed_questions PASSED            [ 64%]
tests/test_questions.py::test_validation_empty_text PASSED               [ 71%]
tests/test_questions.py::test_validation_zero_questions PASSED           [ 78%]
tests/test_questions.py::test_validation_over_limit_questions PASSED     [ 85%]
tests/test_questions.py::test_validation_invalid_question_type PASSED    [ 92%]
tests/test_questions.py::test_validation_invalid_difficulty PASSED       [100%]

============================= 14 passed in 1.53s ==============================
```

---

## 🚀 Future Roadmap
- **v1.1**: Export generated questions directly as printable PDF or CSV.
- **v1.2**: SQLite / PostgreSQL question bank history persistence.
- **v1.3**: Automatic topic detection and difficulty scoring.
