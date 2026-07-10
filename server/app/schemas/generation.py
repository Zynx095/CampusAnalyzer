from typing import Optional

from pydantic import BaseModel, Field, field_validator


ALLOWED_DIMENSIONS = {512, 640, 768, 896, 1024}


class LocalImageGenerationRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Positive generation prompt",
    )

    negative_prompt: str = Field(
        default="",
        max_length=2000,
        description="Optional negative prompt",
    )

    width: int = Field(default=768)
    height: int = Field(default=768)

    seed: Optional[int] = Field(
        default=None,
        ge=0,
        le=0xFFFFFFFFFFFFFFFF,
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Prompt cannot be empty")

        return cleaned

    @field_validator("width", "height")
    @classmethod
    def validate_dimensions(cls, value: int) -> int:
        if value not in ALLOWED_DIMENSIONS:
            raise ValueError(
                f"Dimension must be one of: "
                f"{sorted(ALLOWED_DIMENSIONS)}"
            )

        return value


class LocalImageGenerationResponse(BaseModel):
    provider: str
    status: str
    prompt_id: str
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