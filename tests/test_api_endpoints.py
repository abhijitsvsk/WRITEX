import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.server import app
from src.database.session import get_db
from src.database.base import Base

@pytest.fixture(scope="module")
def test_client():
    """Test client for FastAPI app with shared in-memory test DB."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)

def test_health_endpoint(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert "token_bucket_rate_limiter" in data["features"]

def test_get_job_status_404(test_client):
    response = test_client.get("/api/jobs/non-existent-uuid")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"

def test_format_text_missing_key(test_client):
    response = test_client.post(
        "/api/format_text",
        data={"text": "Sample content to format.", "api_key": ""}
    )
    assert response.status_code in [400, 422]

@patch("src.server.structure_text")
def test_format_text_success(mock_structure, test_client):
    mock_structure.return_value = '[{"type": "paragraph", "text": "Structured test paragraph."}]'

    response = test_client.post(
        "/api/format_text",
        data={
            "text": "Raw unstructured paragraph.",
            "api_key": "test_mock_key",
            "style_name": "Academic",
        }
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert len(response.content) > 1000

def test_format_file_unsupported_format(test_client):
    fake_file = io.BytesIO(b"binary content")
    response = test_client.post(
        "/api/format_file",
        data={"api_key": "mock_key"},
        files={"file": ("test.exe", fake_file, "application/octet-stream")}
    )
    assert response.status_code in [400, 422]
    assert "Unsupported file format" in response.json()["detail"]

def test_format_academic_report_validation_errors(test_client):
    # Missing API key
    response = test_client.post(
        "/api/format_academic_report",
        data={"api_key": "", "team_names": "Alice"}
    )
    assert response.status_code in [400, 422]

    # Missing team names
    response = test_client.post(
        "/api/format_academic_report",
        data={"api_key": "valid_key", "team_names": ""}
    )
    assert response.status_code in [400, 422]

    # Missing both ZIP and GitHub URL
    response = test_client.post(
        "/api/format_academic_report",
        data={"api_key": "valid_key", "team_names": "Alice", "github_url": ""}
    )
    assert response.status_code in [400, 422]
    assert "ZIP file or provide a GitHub URL" in response.json()["detail"]

def test_format_academic_report_end_to_end_success(test_client):
    import zipfile
    from docx import Document

    # Create synthetic project zip
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as z:
        z.writestr("main.py", "def run():\n    print('Hello world')\n")
        z.writestr("utils.py", "def add(a, b):\n    return a + b\n")
    zip_buf.seek(0)

    from src.ai.rate_limiter import TokenBucketLimiter
    fast_limiter = TokenBucketLimiter(capacity=1000.0, refill_rate_per_sec=1000.0)

    with patch("src.ai.report_generator.ReportGenerator.generate_chapter_intro") as mock_intro, \
         patch("src.ai.report_generator.ReportGenerator.generate_subsection_body") as mock_body, \
         patch("src.ai.report_generator.ReportGenerator.generate_section") as mock_sec, \
         patch("src.core.compiler.get_rate_limiter", return_value=fast_limiter):
        
        mock_intro.return_value = "This chapter introduces key concepts."
        mock_body.return_value = "Detailed academic discussion on the system architecture."
        mock_sec.return_value = "Project abstract summarizing findings."

        response = test_client.post(
            "/api/format_academic_report",
            data={
                "api_key": "mock_test_key",
                "title": "Automated Academic Engine",
                "team_names": "Alice Smith, Bob Jones",
                "degree": "B.Tech Computer Science",
                "department": "Computer Science and Engineering",
                "university": "State Technical University",
                "academic_year": "2025–2026",
            },
            files={"proj_zip": ("repo.zip", zip_buf, "application/zip")}
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    job_id = response.headers.get("X-WriteX-Job-ID")
    assert job_id is not None

    # Verify DOCX content
    res_docx = Document(io.BytesIO(response.content))
    assert len(res_docx.paragraphs) > 10

    # Verify Job status in DB
    job_resp = test_client.get(f"/api/jobs/{job_id}")
    assert job_resp.status_code == 200
    job_data = job_resp.json()
    assert job_data["status"] == "COMPLETED"
    assert job_data["progress"] == 100

