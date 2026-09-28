from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON, DateTime, Boolean
import uuid
from datetime import datetime, timezone
from src.database.base import Base, TimestampMixin

class ReportJob(Base, TimestampMixin):
    __tablename__ = "report_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String(32), index=True, nullable=False, default="PENDING")
    progress = Column(Integer, default=0, nullable=False)
    title = Column(String(255))
    degree = Column(String(128))
    university = Column(String(255))
    department = Column(String(255))
    academic_year = Column(String(64))
    output_file_path = Column(String(1024))
    error_message = Column(Text)
    execution_time_seconds = Column(Integer)
    completed_at = Column(DateTime)

class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True)
    title = Column(String(255))
    degree = Column(String(128))
    university = Column(String(255))
    department = Column(String(255))
    academic_year = Column(String(64))
    guide = Column(String(128))
    hod = Column(String(128))
    principal = Column(String(128))
    team_names = Column(JSON)
    tech_stack = Column(JSON)

class GenerationCache(Base, TimestampMixin):
    __tablename__ = "generation_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(64), unique=True, index=True, nullable=False)
    provider = Column(String(64))
    model_name = Column(String(128))
    prompt_preview = Column(Text)
    completion_text = Column(Text)
    hit_count = Column(Integer, default=1, nullable=False)
    last_accessed_at = Column(DateTime, index=True, default=lambda: datetime.now(timezone.utc))

class ConstraintAudit(Base, TimestampMixin):
    __tablename__ = "constraint_audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("report_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    parameter_key = Column(String(128))
    parameter_label = Column(String(255))
    reference_value = Column(String(1024))
    request_value = Column(String(1024))
    resolved_value = Column(String(1024))
    resolution_source = Column(String(128))

class ApiKey(Base, TimestampMixin):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_hash = Column(String(255), unique=True, index=True, nullable=False)
    owner_name = Column(String(128))
    rate_limit_rpm = Column(Integer, default=60, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
