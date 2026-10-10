"""
Configuration settings for ML Engine
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Models
    SENTIMENT_MODEL: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    EMOTION_MODEL: str = "bhadresh-savani/distilbert-base-uncased-emotion"
    SUMMARIZATION_MODEL: str = "sshleifer/distilbart-cnn-12-6"
    ENABLE_EMOTION_MODEL: bool = False
    ENABLE_SUMMARIZATION: bool = False
    
    # Classification calibration
    NEUTRAL_THRESHOLD_MARGIN: float = 0.15  # Score margin below which binary sentiment is calibrated to neutral
    NEUTRAL_MIN_CONFIDENCE: float = 0.58    # Minimum top label confidence to be decisively non-neutral
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5000,http://localhost:5173"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
