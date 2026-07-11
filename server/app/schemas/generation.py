from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

ALLOWED_DIMENSIONS = {512, 640, 768, 896, 1024}

class LocalImageGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000, description="Positive generation prompt")
    mode: str = Field(default="image-generation", description="PRANA AI creative routing mode")
    negative_prompt: str = Field(default="", max_length=2000)
    width: int = Field(default=768)
    height: int = Field(default=768)
    seed: Optional[int] = Field(default=None, ge=0, le=0xFFFFFFFFFFFFFFFF)

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned: raise ValueError("Prompt cannot be empty")
        return cleaned

    @field_validator("width", "height")
    @classmethod
    def validate_dimensions(cls, value: int) -> int:
        if value not in ALLOWED_DIMENSIONS:
            raise ValueError(f"Dimension must be one of: {sorted(ALLOWED_DIMENSIONS)}")
        return value

class LocalImageGenerationResponse(BaseModel):
    provider: str
    status: str
    prompt_id: str
    original_prompt: str
    effective_prompt: str
    mode: str
    model: str
    workflow: str
    asset_url: str
    filename: str
    width: int
    height: int
    seed: int

class LocalGenerationHealthResponse(BaseModel):
    provider: str
    status: str
    base_url: str
    workflow_loaded: bool
    workflow_name: str

class ProjectAsset(BaseModel):
    url: str
    kind: str = "image"

class ProjectRecord(BaseModel):
    id: str
    name: str
    prompt: str
    effective_prompt: Optional[str] = None
    provider: str
    model: str
    seed: int
    width: int
    height: int
    filename: str
    asset_url: str
    mode: str = "image-generation"
    created_at: datetime
    assets: list[ProjectAsset] = Field(default_factory=list)

class ProjectListResponse(BaseModel):
    projects: list[ProjectRecord]
    count: int