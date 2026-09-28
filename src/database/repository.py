from sqlalchemy.orm import Session
from sqlalchemy import update, func, select
from datetime import datetime, timezone, timedelta
import bcrypt
import uuid

from src.database.models import ReportJob, GenerationCache, ApiKey
from src.core.config import settings

class JobRepository:
    @staticmethod
    def create_job(db: Session, **kwargs) -> ReportJob:
        if "id" not in kwargs:
            kwargs["id"] = str(uuid.uuid4())
        kwargs.setdefault("status", "PENDING")
        kwargs.setdefault("progress", 0)
        job = ReportJob(**kwargs)
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_job(db: Session, job_id: str) -> ReportJob | None:
        return db.query(ReportJob).filter(ReportJob.id == job_id).first()

    @staticmethod
    def update_progress(db: Session, job_id: str, status: str, progress: int) -> ReportJob | None:
        job = db.query(ReportJob).filter(ReportJob.id == job_id).first()
        if job:
            job.status = status
            job.progress = progress
            job.updated_at = func.now()
            db.commit()
            db.refresh(job)
        return job

    @staticmethod
    def complete_job(db: Session, job_id: str, output_path: str, execution_time: int) -> ReportJob | None:
        job = db.query(ReportJob).filter(ReportJob.id == job_id).first()
        if job:
            job.status = "COMPLETED"
            job.progress = 100
            job.output_file_path = output_path
            job.execution_time_seconds = execution_time
            job.completed_at = func.now()
            job.updated_at = func.now()
            db.commit()
            db.refresh(job)
        return job

    @staticmethod
    def fail_job(db: Session, job_id: str, error_message: str) -> ReportJob | None:
        job = db.query(ReportJob).filter(ReportJob.id == job_id).first()
        if job:
            job.status = "FAILED"
            job.error_message = error_message
            job.updated_at = func.now()
            db.commit()
            db.refresh(job)
        return job

    @staticmethod
    def reconcile_stale_jobs(db: Session, timeout_minutes: int = 10):
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
        stale_statuses = ["PENDING", "ANALYZING", "COMPILING", "VALIDATING", "FORMATTING"]
        
        db.execute(
            update(ReportJob)
            .where(ReportJob.status.in_(stale_statuses))
            .where(ReportJob.updated_at < cutoff)
            .values(
                status="FAILED",
                error_message="Generation interrupted by system restart or crash",
                updated_at=func.now()
            )
        )
        db.commit()


class CacheRepository:
    @staticmethod
    def get(db: Session, cache_key: str) -> str | None:
        stmt = (
            update(GenerationCache)
            .where(GenerationCache.cache_key == cache_key)
            .values(
                hit_count=GenerationCache.hit_count + 1,
                last_accessed_at=func.now()
            )
            .returning(GenerationCache.completion_text)
        )
        result = db.execute(stmt)
        row = result.fetchone()
        db.commit()
        return row[0] if row else None

    @staticmethod
    def set(db: Session, cache_key: str, provider: str, model_name: str, prompt: str, completion: str):
        existing = db.query(GenerationCache).filter(GenerationCache.cache_key == cache_key).first()
        if existing:
            existing.provider = provider
            existing.model_name = model_name
            existing.prompt_preview = prompt[:1000] if prompt else ""
            existing.completion_text = completion
            existing.last_accessed_at = func.now()
            db.commit()
            return existing

        total_rows = db.query(func.count(GenerationCache.id)).scalar()
        if total_rows >= settings.CACHE_MAX_ROWS:
            excess = total_rows - settings.CACHE_MAX_ROWS + 1
            # SQLite does not support ORDER BY/LIMIT in subqueries inside IN directly without careful handling, but this should work with row_number or direct limit
            oldest = db.query(GenerationCache.id).order_by(GenerationCache.last_accessed_at.asc()).limit(excess).all()
            oldest_ids = [r[0] for r in oldest]
            db.query(GenerationCache).filter(GenerationCache.id.in_(oldest_ids)).delete(synchronize_session=False)

        new_entry = GenerationCache(
            cache_key=cache_key,
            provider=provider,
            model_name=model_name,
            prompt_preview=prompt[:1000] if prompt else "",
            completion_text=completion
        )
        db.add(new_entry)
        db.commit()
        return new_entry


class ApiKeyRepository:
    @staticmethod
    def create_key(db: Session, raw_key: str, owner_name: str, rate_limit_rpm: int = 60) -> ApiKey:
        hashed = bcrypt.hashpw(raw_key.encode('utf-8'), bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)).decode('utf-8')
        key_record = ApiKey(
            key_hash=hashed,
            owner_name=owner_name,
            rate_limit_rpm=rate_limit_rpm
        )
        db.add(key_record)
        db.commit()
        db.refresh(key_record)
        return key_record

    @staticmethod
    def verify_key(db: Session, raw_key: str) -> ApiKey | None:
        # In a real scenario, we'd need to either query by owner or scan. Scanning all keys is slow but let's assume we do it for now if we don't know the owner.
        # Actually, it's better to find a way to avoid full scan, e.g. key format: owner_id.random_bytes. 
        # For simplicity, scanning all active keys.
        keys = db.query(ApiKey).filter(ApiKey.is_active == True).all()
        for key in keys:
            if bcrypt.checkpw(raw_key.encode('utf-8'), key.key_hash.encode('utf-8')):
                return key
        return None
