from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.ml.serving import get_ml_models

router = APIRouter()


class DetectionRequest(BaseModel):
    event_data: Dict[str, Any]


class DetectionResponse(BaseModel):
    risk_score: float
    detection_type: str
    confidence: float
    indicators: List[str]
    recommended_actions: List[str]


class ModelInfo(BaseModel):
    name: str
    version: str
    status: str
    accuracy: float
    last_updated: str


class ModelMetrics(BaseModel):
    inference_time_ms: float
    throughput_events_per_sec: float
    memory_usage_mb: float
    gpu_utilization: float


@router.post("/detect", response_model=DetectionResponse)
async def detect_ransomware(request: DetectionRequest):
    models = get_ml_models()
    if not models.loaded:
        raise HTTPException(status_code=503, detail="ML models not loaded")

    result = await models.detect(request.event_data)
    return result


@router.post("/detect/batch")
async def detect_ransomware_batch(requests: List[DetectionRequest]):
    models = get_ml_models()
    if not models.loaded:
        raise HTTPException(status_code=503, detail="ML models not loaded")

    results = []
    for request in requests:
        result = await models.detect(request.event_data)
        results.append(result)

    return {"results": results}


@router.get("/models", response_model=List[ModelInfo])
async def get_models_info():
    models = get_ml_models()
    return models.get_info()


@router.get("/models/{model_name}/metrics", response_model=ModelMetrics)
async def get_model_metrics(model_name: str):
    models = get_ml_models()
    metrics = models.get_metrics(model_name)
    if not metrics:
        raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
    return metrics


@router.post("/models/{model_name}/retrain")
async def retrain_model(model_name: str):
    models = get_ml_models()
    success = await models.retrain(model_name)
    if success:
        return {"message": f"Model {model_name} retraining started"}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to retrain model {model_name}")


@router.get("/analyze-patterns")
async def analyze_threat_patterns():
    models = get_ml_models()
    patterns = await models.analyze_patterns()
    return patterns


@router.get("/health")
async def ml_health_check():
    models = get_ml_models()
    return {
        "status": "healthy" if models.loaded else "unhealthy",
        "models_loaded": models.loaded,
        "inference_available": models.is_inference_available(),
    }
