from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SAMPLE_TEXT = (
    "Photosynthesis is the process by which green plants and certain other organisms use sunlight "
    "to synthesize foods with the aid of chlorophyll pigments. Photosynthesis in plants generally involves "
    "the green pigment chlorophyll and generates oxygen as a byproduct. Cellular respiration is the inverse process "
    "where cells break down sugar and turn it into energy."
)


def test_root_health_check():
    """Test root GET / returns healthy status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "EduQuestion AI" in data["message"]


def test_health_endpoint():
    """Test /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_generate_mcq_success():
    """Test valid text generating MCQ questions."""
    payload = {
        "text": SAMPLE_TEXT,
        "number_of_questions": 3,
        "question_type": "mcq",
        "difficulty": "easy"
    }
    response = client.post("/api/v1/questions/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_questions"] >= 1
    assert data["source_type"] == "text"
    assert len(data["questions"]) >= 1

    first_q = data["questions"][0]
    assert "question" in first_q
    assert "options" in first_q
    assert "answer" in first_q
    assert "explanation" in first_q
    assert first_q["type"] == "mcq"


def test_generate_short_answer_success():
    """Test generating short answer questions."""
    payload = {
        "text": SAMPLE_TEXT,
        "number_of_questions": 2,
        "question_type": "short_answer",
        "difficulty": "medium"
    }
    response = client.post("/api/v1/questions/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["questions"]) >= 1
    assert data["questions"][0]["type"] == "short_answer"


def test_generate_true_false_success():
    """Test generating true/false questions."""
    payload = {
        "text": SAMPLE_TEXT,
        "number_of_questions": 2,
        "question_type": "true_false",
        "difficulty": "medium"
    }
    response = client.post("/api/v1/questions/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["questions"]) >= 1
    first_q = data["questions"][0]
    assert first_q["type"] == "true_false"
    assert first_q["answer"] in ["True", "False"]


def test_generate_mixed_questions():
    """Test /mixed endpoint generates mixed questions."""
    payload = {
        "text": SAMPLE_TEXT,
        "number_of_questions": 3,
        "difficulty": "medium"
    }
    response = client.post("/api/v1/questions/mixed", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["questions"]) >= 1


def test_validation_empty_text():
    """Test empty text is rejected with validation error."""
    payload = {
        "text": "   ",
        "number_of_questions": 5,
        "question_type": "mcq",
        "difficulty": "easy"
    }
    response = client.post("/api/v1/questions/generate", json=payload)
    assert response.status_code == 422
    assert "Educational material cannot be empty" in response.json()["detail"]


def test_validation_zero_questions():
    """Test 0 questions is rejected (must be >= 1)."""
    payload = {
        "text": SAMPLE_TEXT,
        "number_of_questions": 0,
        "question_type": "mcq",
        "difficulty": "easy"
    }
    response = client.post("/api/v1/questions/generate", json=payload)
    assert response.status_code == 422
    assert "Number of questions must be between 1 and 50" in response.json()["detail"]


def test_validation_over_limit_questions():
    """Test 51 questions is rejected (must be <= 50)."""
    payload = {
        "text": SAMPLE_TEXT,
        "number_of_questions": 51,
        "question_type": "mcq",
        "difficulty": "easy"
    }
    response = client.post("/api/v1/questions/generate", json=payload)
    assert response.status_code == 422
    assert "Number of questions must be between 1 and 50" in response.json()["detail"]


def test_validation_invalid_question_type():
    """Test invalid question type is rejected."""
    payload = {
        "text": SAMPLE_TEXT,
        "number_of_questions": 5,
        "question_type": "essay",
        "difficulty": "easy"
    }
    response = client.post("/api/v1/questions/generate", json=payload)
    assert response.status_code == 422
    assert "Invalid question type" in response.json()["detail"]


def test_validation_invalid_difficulty():
    """Test invalid difficulty level is rejected."""
    payload = {
        "text": SAMPLE_TEXT,
        "number_of_questions": 5,
        "question_type": "mcq",
        "difficulty": "extreme"
    }
    response = client.post("/api/v1/questions/generate", json=payload)
    assert response.status_code == 422
    assert "Invalid difficulty level" in response.json()["detail"]
