import os
import json
import logging
import asyncio
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from fastapi import HTTPException
from app.schemas.campus import CampusAnalysisResponse

logger = logging.getLogger(__name__)

class CampusAnalysisService:
    @staticmethod
    async def analyze_image(image_bytes: bytes, mime_type: str, retries: int = 1) -> CampusAnalysisResponse:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key or api_key == "your_actual_api_key_here":
            logger.error("GEMINI_API_KEY environment variable is missing or invalid.")
            raise HTTPException(
                status_code=500, 
                detail="Vision engine configuration is missing. Please set a valid GEMINI_API_KEY."
            )

        genai.configure(api_key=api_key)

        prompt = """
        You are an expert architectural consultant evaluating a university campus environment.
        Analyze the provided image and return ONLY a valid, strict JSON object.
        Do not hallucinate hidden structures; analyze ONLY what is visible in the provided image.

        Required JSON structure:
        {
          "overall_score": <int 0-100>,
          "green_cover": <int 0-100>,
          "walkability": <int 0-100>,
          "solar_potential": <int 0-100>,
          "parking_efficiency": <int 0-100>,
          "accessibility": <int 0-100>,
          "building_condition": "<string, e.g., 'Excellent', 'Good', 'Fair', 'Poor'>",
          "summary": "<string, concise architectural summary of the visible space>",
          "recommendations": [
              "<string, practical campus upgrade 1 based on visuals>",
              "<string, practical campus upgrade 2 based on visuals>"
          ]
        }
        """

        try:
            # Swapped to flash-lite for 15 requests/minute instead of 5
            model = genai.GenerativeModel('gemini-3.1-flash-lite')
            
            response = await model.generate_content_async(
                contents=[
                    prompt,
                    {"mime_type": mime_type, "data": image_bytes}
                ],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
            parsed_data = json.loads(response.text)
            return CampusAnalysisResponse(**parsed_data)
            
        except ResourceExhausted as exc: # 429 Quota Exceeded Catch
            if retries > 0:
                logger.warning("Gemini API Rate Limit hit. Waiting 12 seconds to automatically retry...")
                await asyncio.sleep(12) # Pauses the backend momentarily to let the Google quota reset
                return await CampusAnalysisService.analyze_image(image_bytes, mime_type, retries=retries - 1)
            else:
                logger.error("Gemini API Rate Limit exhausted after retries.")
                raise HTTPException(
                    status_code=429, 
                    detail="Google Gemini Rate Limit exceeded. Please wait a minute before requesting another analysis."
                ) from exc

        except json.JSONDecodeError as exc:
            logger.error(f"Vision engine returned invalid JSON: {response.text}")
            raise HTTPException(
                status_code=502, 
                detail="Vision engine failed to return strict JSON format."
            ) from exc
            
        except Exception as exc:
            error_message = str(exc)
            logger.exception(f"Gemini API inference failed: {error_message}")
            raise HTTPException(
                status_code=502, 
                detail=f"Google Gemini API Error: {error_message}"
            ) from exc