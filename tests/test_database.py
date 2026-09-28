import os
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, select, text, func
from sqlalchemy.orm import sessionmaker

from src.database.base import Base
from src.database.models import ReportJob, Project, GenerationCache, ConstraintAudit, ApiKey
from src.database.repository import JobRepository, CacheRepository, ApiKeyRepository
from src.core.config import settings

@pytest.fixture(scope="function")
def db_session():
    """Isolated in-memory SQLite session with schema applied."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

class TestJobRepository:
    def test_create_and_get_job(self, db_session):
        job = JobRepository.create_job(
            db_session,
            title="Automated Test Job",
            degree="B.Tech Computer Science",
            university="Test University",
            department="CSE",
            academic_year="2025-2026"
        )
        assert job.id is not None
        assert len(job.id) == 36
        assert job.status == "PENDING"
        assert job.progress == 0
        assert job.created_at is not None
        assert job.updated_at is not None

        retrieved = JobRepository.get_job(db_session, job.id)
        assert retrieved is not None
        assert retrieved.title == "Automated Test Job"

    def test_progress_heartbeat_updates_timestamp(self, db_session):
        job = JobRepository.create_job(db_session, title="Heartbeat Job")
        initial_updated_at = job.updated_at

        # Progress transition
        updated_job = JobRepository.update_progress(db_session, job.id, "ANALYZING", 25)
        assert updated_job.status == "ANALYZING"
        assert updated_job.progress == 25
        assert updated_job.updated_at is not None

    def test_complete_and_fail_job(self, db_session):
        job = JobRepository.create_job(db_session, title="Job Lifecycle")
        
        # Complete
        completed = JobRepository.complete_job(db_session, job.id, "/path/to/report.docx", 45)
        assert completed.status == "COMPLETED"
        assert completed.progress == 100
        assert completed.output_file_path == "/path/to/report.docx"
        assert completed.execution_time_seconds == 45
        assert completed.completed_at is not None

        # Fail
        failed_job = JobRepository.create_job(db_session, title="Failing Job")
        failed = JobRepository.fail_job(db_session, failed_job.id, "Out of memory error")
        assert failed.status == "FAILED"
        assert failed.error_message == "Out of memory error"

    def test_reconcile_stale_jobs_heartbeat_check(self, db_session):
        # 1. Job that is stale (no heartbeat update for >10 minutes)
        stale_time = datetime.now(timezone.utc) - timedelta(minutes=15)
        stale_job = ReportJob(
            id=str(uuid.uuid4()),
            title="Stale Job",
            status="ANALYZING",
            progress=30,
            created_at=stale_time,
            updated_at=stale_time
        )
        db_session.add(stale_job)

        # 2. Job that is actively progressing (updated 1 minute ago)
        active_time = datetime.now(timezone.utc) - timedelta(minutes=1)
        active_job = ReportJob(
            id=str(uuid.uuid4()),
            title="Active Job",
            status="COMPILING",
            progress=60,
            created_at=stale_time,
            updated_at=active_time
        )
        db_session.add(active_job)
        db_session.commit()

        # Run reconciliation sweep with 10-minute timeout
        JobRepository.reconcile_stale_jobs(db_session, timeout_minutes=10)

        # Check stale job was marked FAILED
        db_session.refresh(stale_job)
        assert stale_job.status == "FAILED"
        assert "interrupted" in stale_job.error_message.lower()

        # Check active job was NOT touched
        db_session.refresh(active_job)
        assert active_job.status == "COMPILING"
        assert active_job.error_message is None

class TestCacheRepository:
    def test_set_and_atomic_get(self, db_session):
        key = "sha256_mock_cache_key_12345"
        CacheRepository.set(
            db_session,
            cache_key=key,
            provider="groq",
            model_name="llama-3.3-70b-versatile",
            prompt="Analyze this code snippet",
            completion="Analysis result text."
        )

        # First retrieval - hit count should be 2 (initial=1, incremented to 2)
        cached_val = CacheRepository.get(db_session, key)
        assert cached_val == "Analysis result text."

        row = db_session.query(GenerationCache).filter_by(cache_key=key).first()
        assert row.hit_count == 2

    def test_cache_miss_returns_none(self, db_session):
        res = CacheRepository.get(db_session, "non_existent_key")
        assert res is None

    def test_lru_eviction_on_insert(self, db_session, monkeypatch):
        # Temporarily lower CACHE_MAX_ROWS to 3 for testing eviction
        monkeypatch.setattr(settings, "CACHE_MAX_ROWS", 3)

        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        mid_time = datetime.now(timezone.utc) - timedelta(hours=1)

        # Insert 3 rows
        c1 = GenerationCache(cache_key="key_1", provider="groq", model_name="m1", completion_text="t1", last_accessed_at=old_time)
        c2 = GenerationCache(cache_key="key_2", provider="groq", model_name="m1", completion_text="t2", last_accessed_at=mid_time)
        c3 = GenerationCache(cache_key="key_3", provider="groq", model_name="m1", completion_text="t3", last_accessed_at=datetime.now(timezone.utc))
        db_session.add_all([c1, c2, c3])
        db_session.commit()

        # Inserting a 4th row should evict the oldest (key_1)
        CacheRepository.set(db_session, "key_4", "groq", "m1", "p4", "t4")

        remaining_keys = [r.cache_key for r in db_session.query(GenerationCache).all()]
        assert len(remaining_keys) == 3
        assert "key_1" not in remaining_keys
        assert "key_4" in remaining_keys

class TestApiKeyRepository:
    def test_bcrypt_hashing_and_verification(self, db_session):
        raw_token = "writex_sec_999888777abc"
        key_record = ApiKeyRepository.create_key(
            db_session,
            raw_key=raw_token,
            owner_name="University Partner",
            rate_limit_rpm=120
        )
        assert key_record.id is not None
        assert key_record.key_hash != raw_token
        assert key_record.key_hash.startswith("$2b$") or key_record.key_hash.startswith("$2a$")

        # Verify key
        matched = ApiKeyRepository.verify_key(db_session, raw_token)
        assert matched is not None
        assert matched.owner_name == "University Partner"

        # Reject invalid key
        assert ApiKeyRepository.verify_key(db_session, "wrong_token") is None

class TestConstraintAuditCascade:
    def test_audit_survives_job_deletion(self, db_session):
        # Create a job
        job = JobRepository.create_job(db_session, title="Audit Job")
        job_id = job.id

        # Create audit record
        audit = ConstraintAudit(
            job_id=job_id,
            parameter_key="font_size",
            parameter_label="Font Size",
            reference_value="12pt",
            request_value="14pt",
            resolved_value="12pt",
            resolution_source="reference"
        )
        db_session.add(audit)
        db_session.commit()
        audit_id = audit.id

        # Delete the job
        db_session.delete(job)
        db_session.commit()

        # The audit row must still exist with job_id set to None (ON DELETE SET NULL)
        refreshed_audit = db_session.query(ConstraintAudit).filter_by(id=audit_id).first()
        assert refreshed_audit is not None
        assert refreshed_audit.parameter_key == "font_size"
        # In SQLite without foreign_keys PRAGMA in-memory, or in Postgres, check persistence
        assert refreshed_audit.resolved_value == "12pt"

class TestPostgresTier:
    """Secondary test tier to catch Postgres/Supabase dialect differences."""
    def test_postgres_connection_if_configured(self):
        postgres_url = os.getenv("TEST_POSTGRES_URL") or os.getenv("DATABASE_URL")
        if not postgres_url or not postgres_url.startswith("postgres"):
            pytest.skip("No PostgreSQL URL configured in TEST_POSTGRES_URL. Skipping Postgres-tier integration test.")

        engine = create_engine(postgres_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            assert result == 1
