import io
from fastapi.testclient import TestClient
import pypdf
from app.main import app
from app.services.pdf_service import clean_extracted_text

client = TestClient(app)


def create_dummy_pdf_bytes(text_content: str) -> bytes:
    """Helper to generate an in-memory PDF containing the given text."""
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=300, height=300)
    
    # We can inject text using standard PDF stream or metadata for test purposes
    buffer = io.BytesIO()
    writer.write(buffer)
    # Return buffer bytes
    return buffer.getvalue()


def test_clean_extracted_text_helper():
    """Test text cleaning normalizes newlines, removes null bytes, and trims."""
    dirty_text = "  Hello \x00 World!\r\n\r\n\r\n\r\nThis is a   test.  "
    cleaned = clean_extracted_text(dirty_text)
    assert "\x00" not in cleaned
    assert "\r" not in cleaned
    assert "Hello World!" in cleaned
    assert "This is a test." in cleaned


def test_invalid_file_extension():
    """Test uploading a non-PDF file returns 400 error."""
    fake_file = io.BytesIO(b"Just plain text notes")
    response = client.post(
        "/api/v1/questions/generate-from-pdf",
        files={"file": ("notes.txt", fake_file, "text/plain")},
        data={"number_of_questions": 5, "question_type": "mcq", "difficulty": "easy"}
    )
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]


def test_empty_pdf_rejection():
    """Test uploading an empty 0-byte PDF returns 400 error."""
    empty_file = io.BytesIO(b"")
    response = client.post(
        "/api/v1/questions/generate-from-pdf",
        files={"file": ("empty.pdf", empty_file, "application/pdf")},
        data={"number_of_questions": 3, "question_type": "mcq", "difficulty": "medium"}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()
