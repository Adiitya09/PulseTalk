"""
Analysis router - endpoints for sentiment and emotion analysis
"""

import logging
from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import (
    AnalysisRequest,
    BatchAnalysisRequest,
    AnalysisResult,
    BatchAnalysisResult
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=AnalysisResult)
@router.post("/", response_model=AnalysisResult)
async def analyze_text(request: Request, body: AnalysisRequest):
    """
    Analyze a single text for sentiment and emotions.
    
    Returns sentiment label, confidence score, and emotion vector.
    """
    try:
        ml_service = request.app.state.ml_service
        
        if not ml_service:
            raise HTTPException(
                status_code=503,
                detail="ML service not available"
            )
        
        logger.info(f"Analyzing text of length {len(body.text)}")
        result = ml_service.analyze_text(body.text)
        
        return result
        
    except HTTPException:
        raise
    except ValueError as ve:
        logger.warning(f"Input validation error: {ve}")
        raise HTTPException(
            status_code=422,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/batch", response_model=BatchAnalysisResult)
async def analyze_batch(request: Request, body: BatchAnalysisRequest):
    """
    Analyze multiple texts for sentiment and emotions.
    
    Maximum 100 texts per batch request.
    """
    try:
        ml_service = request.app.state.ml_service
        
        if not ml_service:
            raise HTTPException(
                status_code=503,
                detail="ML service not available"
            )
        
        logger.info(f"Batch analyzing {len(body.texts)} texts")
        results = ml_service.analyze_batch(body.texts)
        
        return BatchAnalysisResult(
            results=results,
            total=len(results)
        )
        
    except HTTPException:
        raise
    except ValueError as ve:
        logger.warning(f"Batch validation error: {ve}")
        raise HTTPException(
            status_code=422,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch analysis failed: {str(e)}"
        )
