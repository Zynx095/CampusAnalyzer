from fastapi import APIRouter

from app.schemas.generation import (
    LocalGenerationHealthResponse,
    LocalImageGenerationRequest,
    LocalImageGenerationResponse,
)
from app.services.comfyui_provider import (
    comfyui_provider,
)


router = APIRouter()


@router.get(
    "/health",
    response_model=LocalGenerationHealthResponse,
)
async def local_generation_health():
    return await comfyui_provider.health()


@router.post(
    "/image",
    response_model=LocalImageGenerationResponse,
)
async def generate_local_image(
    request: LocalImageGenerationRequest,
):
    return await comfyui_provider.generate_image(
        prompt=request.prompt,
        negative_prompt=request.negative_prompt,
        width=request.width,
        height=request.height,
        seed=request.seed,
    )