from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.campus import CampusAnalysisResponse
from app.services.campus_analysis import CampusAnalysisService

router = APIRouter(prefix="/api/campus", tags=["campus"])

MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB limit

@router.post("/analyze", response_model=CampusAnalysisResponse)
async def analyze_campus(image: UploadFile = File(...)):
    # 1. Validate MIME type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file format. Please upload an image."
        )

    # 2. Read and validate file size securely
    contents = await image.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413, 
            detail="Payload Too Large. Maximum allowed image size is 15 MB."
        )
    
    if len(contents) == 0:
        raise HTTPException(
            status_code=400, 
            detail="Uploaded file is empty."
        )

    # 3. Process via Gemini Vision
    return await CampusAnalysisService.analyze_image(contents, image.content_type)