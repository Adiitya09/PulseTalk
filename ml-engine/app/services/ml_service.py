"""
ML Service - Sentiment and Emotion Analysis using Hugging Face Transformers
Includes NLP preprocessing, robust multi-version pipeline extraction, and neutral calibration.
"""

import logging
from typing import Dict, List, Any, Optional

from transformers import pipeline

from app.config import settings
from app.models.schemas import AnalysisResult, EmotionScore
from app.services.preprocessor import TextPreprocessor

logger = logging.getLogger(__name__)


class MLService:
    """
    Machine Learning service for sentiment and emotion analysis.
    Loads models lazily or at startup and provides robust inference.
    """
    
    def __init__(self):
        self.sentiment_pipeline = None
        self.emotion_pipeline = None
        self.summarization_pipeline = None
        self.models_loaded = False
    
    def load_models(self) -> None:
        """Load models based on enabled feature flags"""
        try:
            logger.info(f"Loading sentiment model: {settings.SENTIMENT_MODEL}")
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=settings.SENTIMENT_MODEL,
                top_k=None  # Return all labels with scores
            )
            
            if settings.ENABLE_EMOTION_MODEL:
                logger.info(f"Loading emotion model: {settings.EMOTION_MODEL}")
                self.emotion_pipeline = pipeline(
                    "text-classification",
                    model=settings.EMOTION_MODEL,
                    top_k=None  # Return all emotions with scores
                )
            else:
                logger.info("Emotion model disabled (set ENABLE_EMOTION_MODEL=True to enable)")
            
            if settings.ENABLE_SUMMARIZATION:
                logger.info(f"Loading summarization model: {settings.SUMMARIZATION_MODEL}")
                self.summarization_pipeline = pipeline(
                    "summarization",
                    model=settings.SUMMARIZATION_MODEL
                )
            else:
                logger.info("Summarization disabled (set ENABLE_SUMMARIZATION=True to enable)")
            
            self.models_loaded = True
            logger.info("All configured models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise RuntimeError(f"Model loading failed: {e}")

    def ensure_models_loaded(self) -> None:
        """Lazy-load models on first request to avoid startup OOM or delays."""
        if not self.models_loaded:
            self.load_models()

    def _extract_pipeline_items(self, raw_result: Any) -> List[Dict[str, Any]]:
        """
        Safely normalize Hugging Face pipeline outputs across different versions
        and single/batch call structures.
        """
        if not raw_result:
            return []
        
        # Handle [[{...}, {...}]] or [{...}, {...}] or [{'label': ..., 'score': ...}]
        if isinstance(raw_result, list):
            if len(raw_result) > 0 and isinstance(raw_result[0], list):
                return raw_result[0]
            if len(raw_result) > 0 and isinstance(raw_result[0], dict):
                return raw_result
        elif isinstance(raw_result, dict):
            return [raw_result]
            
        return []
    
    def _normalize_sentiment(self, label: str) -> str:
        """Normalize sentiment labels to standard format"""
        label_lower = label.lower().strip()
        if label_lower in ["positive", "pos", "1", "label_1"]:
            return "positive"
        elif label_lower in ["negative", "neg", "0", "label_0"]:
            return "negative"
        else:
            return "neutral"
    
    def _get_sentiment_result(self, prepared_text: str) -> Dict[str, Any]:
        """
        Run sentiment analysis and calibrate for positive, negative, and neutral classes.
        """
        raw = self.sentiment_pipeline(prepared_text, truncation=True, max_length=512)
        items = self._extract_pipeline_items(raw)
        
        if items:
            # Map labels to scores
            scores_by_label = {}
            for item in items:
                norm_label = self._normalize_sentiment(item.get("label", ""))
                scores_by_label[norm_label] = float(item.get("score", 0.0))
            
            pos_score = scores_by_label.get("positive", 0.0)
            neg_score = scores_by_label.get("negative", 0.0)
            neu_score = scores_by_label.get("neutral", 0.0)
            
            # 1. Native 3-class model path (e.g. twitter-roberta-base-sentiment-latest)
            if neu_score > 0.0:
                if neu_score >= pos_score and neu_score >= neg_score:
                    return {
                        "sentiment": "neutral",
                        "sentiment_score": neu_score,
                        "pos_score": pos_score,
                        "neg_score": neg_score,
                        "is_calibrated_neutral": False
                    }
                elif pos_score >= neg_score:
                    return {
                        "sentiment": "positive",
                        "sentiment_score": pos_score,
                        "pos_score": pos_score,
                        "neg_score": neg_score,
                        "is_calibrated_neutral": False
                    }
                else:
                    return {
                        "sentiment": "negative",
                        "sentiment_score": neg_score,
                        "pos_score": pos_score,
                        "neg_score": neg_score,
                        "is_calibrated_neutral": False
                    }

            # 2. Binary model fallback (e.g. SST-2 without native neutral class)
            margin = abs(pos_score - neg_score)
            top_score = max(pos_score, neg_score)

            if margin < settings.NEUTRAL_THRESHOLD_MARGIN or top_score < settings.NEUTRAL_MIN_CONFIDENCE:
                # Calibrated low-confidence binary prediction
                calibrated_neutral_score = max(0.5, 1.0 - margin)
                return {
                    "sentiment": "neutral",
                    "sentiment_score": calibrated_neutral_score,
                    "pos_score": pos_score,
                    "neg_score": neg_score,
                    "is_calibrated_neutral": True
                }

            if pos_score >= neg_score:
                return {
                    "sentiment": "positive",
                    "sentiment_score": pos_score,
                    "pos_score": pos_score,
                    "neg_score": neg_score,
                    "is_calibrated_neutral": False
                }
            else:
                return {
                    "sentiment": "negative",
                    "sentiment_score": neg_score,
                    "pos_score": pos_score,
                    "neg_score": neg_score,
                    "is_calibrated_neutral": False
                }
        
        return {
            "sentiment": "neutral",
            "sentiment_score": 0.5,
            "pos_score": 0.5,
            "neg_score": 0.5
        }
    
    def _get_emotion_result(self, prepared_text: str) -> Dict[str, Any]:
        """Get emotion analysis result for text"""
        if not settings.ENABLE_EMOTION_MODEL or self.emotion_pipeline is None:
            return {
                "emotions": [EmotionScore(emotion="neutral", score=1.0)],
                "dominant_emotion": "neutral",
                "is_model_enabled": False
            }

        raw = self.emotion_pipeline(prepared_text, truncation=True, max_length=512)
        items = self._extract_pipeline_items(raw)
        
        emotions = []
        dominant_emotion = "neutral"
        max_score = 0.0
        
        for item in items:
            emotion = str(item.get("label", "neutral")).lower()
            score = float(item.get("score", 0.0))
            emotions.append(EmotionScore(emotion=emotion, score=round(score, 4)))
            
            if score > max_score:
                max_score = score
                dominant_emotion = emotion
        
        if not emotions:
            emotions = [EmotionScore(emotion="neutral", score=1.0)]
            dominant_emotion = "neutral"
        else:
            emotions.sort(key=lambda x: x.score, reverse=True)
        
        return {
            "emotions": emotions,
            "dominant_emotion": dominant_emotion,
            "is_model_enabled": True
        }

    def _get_summary(self, raw_text: str) -> Optional[str]:
        """Generate a summary of the text if summarization is enabled"""
        if not settings.ENABLE_SUMMARIZATION or self.summarization_pipeline is None:
            return None

        if len(raw_text.strip()) < 50:
            return None
            
        try:
            input_text = raw_text[:4000]
            summary_results = self.summarization_pipeline(
                input_text, 
                truncation=True, 
                max_length=150, 
                min_length=30, 
                do_sample=False
            )
            
            if summary_results and len(summary_results) > 0:
                return summary_results[0].get("summary_text")
            
        except Exception as e:
            logger.warning(f"Summarization failed: {e}")
            return None
            
        return None
    
    def analyze_text(self, text: str) -> AnalysisResult:
        """
        Analyze a single text for sentiment, emotions, and summary.
        
        Args:
            text: Raw input text
            
        Returns:
            AnalysisResult with sentiment, score, confidence, emotions, and summary
            
        Raises:
            ValueError: If input is empty or invalid
        """
        self.ensure_models_loaded()
        
        # 1. Preprocess and validate input
        prepared_text = TextPreprocessor.prepare_for_transformer(text)
        
        # 2. Get sentiment analysis with neutral calibration
        sentiment_result = self._get_sentiment_result(prepared_text)
        
        # 3. Get emotion analysis
        emotion_result = self._get_emotion_result(prepared_text)
        
        # 4. Get summary if enabled
        summary = self._get_summary(text)
        
        # 5. Calculate overall confidence accurately
        sentiment_score = sentiment_result["sentiment_score"]
        if emotion_result.get("is_model_enabled", False):
            dominant_emotion_score = emotion_result["emotions"][0].score if emotion_result["emotions"] else 0.5
            confidence = (sentiment_score + dominant_emotion_score) / 2
        else:
            # When emotion model is disabled, do not dilute sentiment confidence
            confidence = sentiment_score
        
        return AnalysisResult(
            text=text,
            sentiment=sentiment_result["sentiment"],
            sentiment_score=round(sentiment_score, 4),
            confidence=round(confidence, 4),
            emotions=emotion_result["emotions"],
            dominant_emotion=emotion_result["dominant_emotion"],
            summary=summary
        )
    
    def analyze_batch(self, texts: List[str]) -> List[AnalysisResult]:
        """
        Analyze multiple texts in batch.
        """
        if not texts:
            raise ValueError("Input texts list cannot be empty.")
            
        return [self.analyze_text(text) for text in texts]
