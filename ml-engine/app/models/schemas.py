"""
Pydantic models for request/response schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class EmotionScore(BaseModel):
    """Individual emotion score"""
    emotion: str = Field(..., description="Emotion label")
    score: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")


class AnalysisRequest(BaseModel):
    """Request model for single text analysis"""
    text: str = Field(..., min_length=1, max_length=100000, description="Text to analyze")

    @field_validator("text")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Input text cannot be empty or contain only whitespace.")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "I love this product! It exceeded all my expectations."
            }
        }
    )


class BatchAnalysisRequest(BaseModel):
    """Request model for batch text analysis"""
    texts: List[str] = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="List of texts to analyze"
    )

    @field_validator("texts")
    @classmethod
    def validate_texts(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Texts list cannot be empty.")
        for idx, item in enumerate(v):
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"Text item at index {idx} cannot be empty or contain only whitespace.")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "texts": [
                    "I love this product!",
                    "This is terrible.",
                    "It's okay, nothing special."
                ]
            }
        }
    )


class AnalysisResult(BaseModel):
    """Response model for analysis result"""
    text: str = Field(..., description="Original text")
    sentiment: str = Field(..., description="Sentiment label (positive/negative/neutral)")
    sentiment_score: float = Field(..., ge=0, le=1, description="Sentiment confidence score")
    confidence: float = Field(..., ge=0, le=1, description="Overall confidence")
    emotions: List[EmotionScore] = Field(..., description="Emotion scores")
    dominant_emotion: str = Field(..., description="Most prominent emotion")
    summary: Optional[str] = Field(None, description="Comprehensive summary of the content")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "I love this product!",
                "sentiment": "positive",
                "sentiment_score": 0.98,
                "confidence": 0.95,
                "emotions": [
                    {"emotion": "joy", "score": 0.85},
                    {"emotion": "surprise", "score": 0.08},
                    {"emotion": "neutral", "score": 0.04},
                    {"emotion": "sadness", "score": 0.01},
                    {"emotion": "anger", "score": 0.01},
                    {"emotion": "fear", "score": 0.01}
                ],
                "dominant_emotion": "joy"
            }
        }
    )


class BatchAnalysisResult(BaseModel):
    """Response model for batch analysis"""
    results: List[AnalysisResult] = Field(..., description="List of analysis results")
    total: int = Field(..., description="Total number of texts analyzed")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
