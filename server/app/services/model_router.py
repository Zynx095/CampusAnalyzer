from typing import Dict, Any

class ModelRouter:
    """
    Registry for PRANA multi-model AI routing with dedicated node tracking maps.
    Tracks exact node IDs specific to each workflow file format configuration.
    """
    PIPELINES: Dict[str, Dict[str, Any]] = {
        "image-generation": {
            "target_model": "flux1-schnell-fp8.safetensors",
            "fallback_model": "flux1-schnell-fp8.safetensors",
            "target_workflow": "prana_flux_schnell_api.json",
            "fallback_workflow": "prana_flux_schnell_api.json",
            "max_dim": 1024,
            "nodes": {
                "positive_prompt": "6",
                "negative_prompt": "33",
                "sampler": "31",
                "latent": "27",
                "output": "9"
            }
        },
        "campus-vision": {
            "target_model": "flux1-schnell-fp8.safetensors",
            "fallback_model": "flux1-schnell-fp8.safetensors",
            "target_workflow": "prana_flux_schnell_api.json",
            "fallback_workflow": "prana_flux_schnell_api.json",
            "max_dim": 1024,
            "nodes": {
                "positive_prompt": "6",
                "negative_prompt": "33",
                "sampler": "31",
                "latent": "27",
                "output": "9"
            }
        },
        "poster-studio": {
            "target_model": "Qwen-Image Q4_K_S GGUF",
            "fallback_model": "flux1-schnell-fp8.safetensors (Fallback)",
            "target_workflow": "prana_poster_studio_api.json",
            "fallback_workflow": "prana_flux_schnell_api.json",
            "max_dim": 1024,
            "nodes": {
                "positive_prompt": "6",
                "negative_prompt": "7",
                "sampler": "3",
                "latent": "58",
                "output": "60"
            }
        },
        "brand-concept": {
            "target_model": "flux1-schnell-fp8.safetensors",
            "fallback_model": "flux1-schnell-fp8.safetensors",
            "target_workflow": "prana_flux_schnell_api.json",
            "fallback_workflow": "prana_flux_schnell_api.json",
            "max_dim": 1024,
            "nodes": {
                "positive_prompt": "6",
                "negative_prompt": "33",
                "sampler": "31",
                "latent": "27",
                "output": "9"
            }
        }
    }

    @classmethod
    def get_pipeline(cls, mode: str | None) -> Dict[str, Any]:
        if not mode or mode not in cls.PIPELINES:
            return cls.PIPELINES["image-generation"]
        return cls.PIPELINES[mode]