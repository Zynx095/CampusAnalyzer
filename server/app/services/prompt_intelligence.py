import logging

logger = logging.getLogger(__name__)

class PromptIntelligence:
    """
    Deterministic domain-specific prompt enhancement for PRANA.
    Currently uses programmatic rules, with prepared slots for local Ollama integration.
    """
    @staticmethod
    def enhance_deterministic(prompt: str, mode: str) -> str:
        clean_prompt = prompt.strip()
        
        # Contextual intelligence trigger based on user runtime environment
        blr_context = ""
        if any(trigger in clean_prompt.lower() for trigger in ["bengaluru", "bangalore", "campus"]):
            blr_context = ", matching Bengaluru tropical savanna climate, monsoon-resilient structural features"

        if mode == "campus-vision":
            return (
                f"{clean_prompt}. Architectural visualization, photorealistic, adaptive reuse, "
                f"preservation of existing structural elements, climate-responsive design{blr_context}, "
                f"shaded circulation, passive cooling corridors, solar infrastructure, rainwater harvesting setups, "
                f"universal accessibility, premium materials, high architectural precision."
            )
            
        elif mode == "poster-studio":
            return (
                f"{clean_prompt}. Professional graphic design poster, explicit content hierarchy, strong typography "
                f"intent, crisp clean composition, intentional use of negative space, bold visual focal point, "
                f"editorial print layout, premium marketing campaign direction."
            )
            
        elif mode == "brand-concept":
            return (
                f"{clean_prompt}. Premium brand identity concept, professional visual system, distinctive identity territory, "
                f"iconic symbol language, cohesive color palette direction, stark typography personality, "
                f"mockup application context, visual system consistency, corporate brand mood."
            )
            
        return clean_prompt

    @staticmethod
    async def enhance_with_ollama(prompt: str, mode: str) -> str:
        """
        [PENDING OLLAMA INSTALLATION]
        Future integration slot for passing prompts to a local small LLM (e.g., Llama 3 8B or Phi-3) 
        to generate highly nuanced prompt expansions.
        """
        # TODO: Implement httpx call to http://127.0.0.1:11434/api/generate once Ollama is ready
        logger.info("Ollama is not yet active. Falling back to deterministic intelligence.")
        return PromptIntelligence.enhance_deterministic(prompt, mode)