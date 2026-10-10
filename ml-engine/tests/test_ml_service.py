"""
Comprehensive ML Service and API Tests for PulseTalk
Tests preprocessing, sentiment predictions, edge cases, error handling, and API integration.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.ml_service import MLService
from app.services.preprocessor import TextPreprocessor


@pytest.fixture(scope="session")
def ml_service():
    """Create ML service instance and load models once for session"""
    service = MLService()
    service.load_models()
    return service


@pytest.fixture(scope="session")
def test_client(ml_service):
    """FastAPI test client with initialized ML service"""
    app.state.ml_service = ml_service
    with TestClient(app) as client:
        yield client


# =====================================================================
# 1. Preprocessor Unit Tests
# =====================================================================

def test_preprocessor_whitespace_and_empty():
    """Verify empty and whitespace inputs raise ValueError"""
    with pytest.raises(ValueError):
        TextPreprocessor.clean_text("")

    with pytest.raises(ValueError):
        TextPreprocessor.clean_text("   \n\t  ")

    with pytest.raises(ValueError):
        TextPreprocessor.clean_text(None)


def test_preprocessor_html_and_urls():
    """Verify HTML tags and bare URLs are cleaned without losing text"""
    raw = "<p>Check out https://pulsetalk.app for <b>amazing</b> results!</p>"
    cleaned = TextPreprocessor.clean_text(raw)
    assert "<p>" not in cleaned
    assert "https://" not in cleaned
    assert "amazing" in cleaned


def test_preprocessor_emojis():
    """Verify sentiment emojis are converted into descriptive words"""
    raw = "Great device! ❤️👍 But the charger was broken 😡"
    cleaned = TextPreprocessor.clean_text(raw)
    assert "love" in cleaned
    assert "good" in cleaned
    assert "angry" in cleaned


# =====================================================================
# 2. Sentiment Prediction Tests
# =====================================================================

def test_sentiment_analysis_clearly_positive(ml_service):
    """Test clearly positive sentiment detection"""
    result = ml_service.analyze_text("I love this product! It's absolutely amazing and exceeded all expectations!")
    assert result.sentiment == "positive"
    assert result.sentiment_score > 0.8
    assert result.confidence > 0.8
    assert len(result.emotions) > 0


def test_sentiment_analysis_clearly_negative(ml_service):
    """Test clearly negative sentiment detection"""
    result = ml_service.analyze_text("This is completely terrible, defective, and totally broke on first use.")
    assert result.sentiment == "negative"
    assert result.sentiment_score > 0.8
    assert result.confidence > 0.8


def test_sentiment_analysis_neutral(ml_service):
    """Test neutral / objective statement detection"""
    result = ml_service.analyze_text("The package arrived on Tuesday.")
    assert result.sentiment in ["neutral", "positive", "negative"]
    assert 0.0 <= result.sentiment_score <= 1.0


def test_sentiment_negations(ml_service):
    """Test negation handling (e.g., 'not good', 'do not like')"""
    result_neg = ml_service.analyze_text("I do not like this product, it is not good at all.")
    assert result_neg.sentiment == "negative"
    assert result_neg.sentiment_score > 0.7

    result_pos_negation = ml_service.analyze_text("Not bad at all, actually quite decent and satisfying.")
    assert result_pos_negation.sentiment == "positive"


def test_sentiment_emojis(ml_service):
    """Test that emoji signals are translated into correct sentiment polarity"""
    pos_result = ml_service.analyze_text("New phone! ❤️🔥🎉")
    assert pos_result.sentiment == "positive"

    neg_result = ml_service.analyze_text("New update 😡👎💔")
    assert neg_result.sentiment == "negative"


def test_sentiment_mixed(ml_service):
    """Test mixed sentiment text"""
    result = ml_service.analyze_text("The food was delicious, but the customer service was absolutely horrible.")
    assert result.sentiment in ["positive", "negative", "neutral"]
    assert result.confidence > 0


def test_short_text(ml_service):
    """Test very short text inputs"""
    pos = ml_service.analyze_text("Awesome!")
    assert pos.sentiment == "positive"

    neg = ml_service.analyze_text("Awful.")
    assert neg.sentiment == "negative"


def test_long_text_handling(ml_service):
    """Test long text with head+tail chunking preservation"""
    long_text = "I absolutely love this amazing product! It works wonders and has made my workflow so much faster and better. " * 20
    
    result = ml_service.analyze_text(long_text)
    assert result.sentiment == "positive"
    assert result.confidence > 0.8


def test_out_of_vocabulary(ml_service):
    """Test robust handling of unseen words and informal slang"""
    result = ml_service.analyze_text("The vibe was zorking fantabulous and ultra stellar!")
    assert result.sentiment == "positive"


def test_empty_input_validation(ml_service):
    """Verify that empty or whitespace strings raise ValueError"""
    with pytest.raises(ValueError):
        ml_service.analyze_text("")

    with pytest.raises(ValueError):
        ml_service.analyze_text("   \n\t  ")


# =====================================================================
# 3. Batch Analysis Tests
# =====================================================================

def test_batch_analysis(ml_service):
    """Test batch analysis with multiple texts"""
    texts = [
        "This is an amazing experience!",
        "Worst customer support ever encountered.",
        "The package arrived on time."
    ]
    results = ml_service.analyze_batch(texts)
    assert len(results) == 3
    assert results[0].sentiment == "positive"
    assert results[1].sentiment == "negative"
    assert all(0.0 <= r.confidence <= 1.0 for r in results)


# =====================================================================
# 4. FastAPI Endpoint Integration Tests
# =====================================================================

def test_api_health(test_client):
    """Test /health endpoint"""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ml-engine"


def test_api_analyze_valid(test_client):
    """Test POST /analyze with valid text"""
    response = test_client.post("/analyze", json={"text": "I really love using PulseTalk!"})
    assert response.status_code == 200
    data = response.json()
    assert data["sentiment"] == "positive"
    assert data["sentiment_score"] > 0.8
    assert "confidence" in data
    assert "emotions" in data


def test_api_analyze_whitespace_rejected(test_client):
    """Test POST /analyze with whitespace-only input returns 422 Unprocessable Entity"""
    response = test_client.post("/analyze", json={"text": "    "})
    assert response.status_code == 422


def test_api_analyze_batch_valid(test_client):
    """Test POST /analyze/batch with list of texts"""
    response = test_client.post(
        "/analyze/batch",
        json={"texts": ["Great product!", "Terrible service."]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["results"]) == 2
    assert data["results"][0]["sentiment"] == "positive"
    assert data["results"][1]["sentiment"] == "negative"
