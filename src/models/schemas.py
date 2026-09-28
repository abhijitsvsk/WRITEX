from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    title: Optional[str] = None
    output_file_path: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_seconds: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class ConflictItem(BaseModel):
    parameter_key: str
    parameter_label: str
    request_value: Any
    reference_value: Any

class ConflictResponse(BaseModel):
    conflicts: List[ConflictItem]

class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    features: List[str]

class ApiKeyCreateRequest(BaseModel):
    owner_name: str = Field(..., min_length=2, max_length=128)
    rate_limit_rpm: int = Field(default=60, ge=1, le=1000)

class ApiKeyResponse(BaseModel):
    raw_key: str
    owner_name: str
    rate_limit_rpm: int
    created_at: datetime
