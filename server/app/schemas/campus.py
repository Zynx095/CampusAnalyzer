from pydantic import BaseModel

class CampusAnalysisResponse(BaseModel):
    overall_score: int
    green_cover: int
    walkability: int
    solar_potential: int
    parking_efficiency: int
    accessibility: int
    building_condition: str
    summary: str
    recommendations: list[str]