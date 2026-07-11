from fastapi import APIRouter
from app.schemas.generation import (
    LocalGenerationHealthResponse,
    LocalImageGenerationRequest,
    LocalImageGenerationResponse,
)
from app.services.comfyui_provider import comfyui_provider
from app.services.model_router import ModelRouter
from app.services.prompt_intelligence import PromptIntelligence

router = APIRouter()

@router.get("/health", response_model=LocalGenerationHealthResponse)
async def local_generation_health():
    return await comfyui_provider.health()

@router.post("/image", response_model=LocalImageGenerationResponse)
async def generate_local_image(request: LocalImageGenerationRequest):
    # Retrieve configuration pipeline map context matching incoming runtime mode parameters
    pipeline = ModelRouter.get_pipeline(request.mode)
    
    # Process text criteria mutations
    effective_prompt = PromptIntelligence.enhance_deterministic(request.prompt, request.mode)
    
    safe_width = min(request.width, pipeline["max_dim"])
    safe_height = min(request.height, pipeline["max_dim"])

    return await comfyui_provider.generate_image(
        prompt=request.prompt,
        effective_prompt=effective_prompt,
        negative_prompt=request.negative_prompt,
        width=safe_width,
        height=safe_height,
        seed=request.seed,
        mode=request.mode,
        pipeline=pipeline
    )