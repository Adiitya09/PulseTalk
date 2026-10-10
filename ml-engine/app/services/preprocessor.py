"""
Text Preprocessing Pipeline for PulseTalk Sentiment Analysis
Preserves contextual nuances, handles emojis, cleans HTML/URLs, and validates input.
"""

import html
import re
from typing import Optional


# Comprehensive mapping of sentiment and emotion-rich emojis to textual tokens
# Padded with spaces to avoid concatenating with adjacent text
EMOJI_SENTIMENT_MAP = {
    # Positive / Love / Joy / Excitement
    "❤️": " love ",
    "💖": " love ",
    "💗": " love ",
    "💓": " love ",
    "💕": " love ",
    "😍": " adore ",
    "🥰": " adore ",
    "😘": " love ",
    "😊": " happy ",
    "😃": " happy ",
    "😄": " happy ",
    "😁": " happy ",
    "😀": " happy ",
    "🥳": " celebrate ",
    "🎉": " celebrate ",
    "✨": " great ",
    "🔥": " fire awesome ",
    "💯": " perfect 100 ",
    "👍": " good thumbs up ",
    "👏": " applaud great ",
    "🙌": " praise awesome ",
    "⭐": " excellent ",
    "🌟": " excellent ",
    "🤩": " amazed awesome ",
    "😎": " cool ",
    
    # Negative / Anger / Disgust / Sadness
    "😡": " angry furious ",
    "😠": " angry annoyed ",
    "🤬": " angry cursing ",
    "👿": " angry evil ",
    "👎": " bad thumbs down ",
    "💩": " terrible crap ",
    "💔": " broken heartbroken ",
    "😢": " sad crying ",
    "😭": " sad weeping ",
    "😞": " disappointed sad ",
    "😔": " depressed sad ",
    "😒": " unamused annoyed ",
    "🤮": " disgusted vomiting ",
    "🤢": " disgusted nauseated ",
    "🙄": " sarcastic eye roll ",
    "💀": " dead bad ",
    "😤": " frustrated angry ",
    " terrible ": " terrible ",
}

# Regex patterns
HTML_TAG_RE = re.compile(r"<[^>]+>")
URL_RE = re.compile(r"https?://\S+|www\.\S+")
MENTION_RE = re.compile(r"@[\w_]+")
HASHTAG_RE = re.compile(r"#([\w_]+)")
CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
MULTI_SPACE_RE = re.compile(r"[ \t]+")
MULTI_NEWLINE_RE = re.compile(r"\n{3,}")


class TextPreprocessor:
    """
    NLP Preprocessor specifically tuned for Transformer-based Sentiment Analysis.
    """

    @classmethod
    def clean_text(cls, text: str) -> str:
        """
        Clean, normalize and prepare text for sentiment analysis inference.
        
        Args:
            text: Raw input text
            
        Returns:
            Normalized string retaining sentiment signals, emojis and punctuation
            
        Raises:
            ValueError: If input is None, non-string, or empty/whitespace only
        """
        if text is None or not isinstance(text, str):
            raise ValueError("Input text must be a non-empty string.")
        
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("Input text cannot be empty or contain only whitespace.")

        # 1. Decode HTML entities (&amp; -> &, &quot; -> ", etc.)
        cleaned = html.unescape(cleaned)

        # 2. Strip HTML tags but keep content inside
        cleaned = HTML_TAG_RE.sub(" ", cleaned)

        # 3. Strip non-printable control characters
        cleaned = CONTROL_CHARS_RE.sub("", cleaned)

        # 4. Remove bare URLs that consume token capacity without sentiment value
        cleaned = URL_RE.sub(" ", cleaned)

        # 5. Normalize user mentions (@username -> @user)
        cleaned = MENTION_RE.sub("@user", cleaned)

        # 6. Extract hashtag words (#awesome -> awesome) to preserve vocabulary match
        cleaned = HASHTAG_RE.sub(r"\1", cleaned)

        # 7. Convert sentiment emojis to text equivalents so uncased models do not map them to [UNK]
        for emoji_char, replacement in EMOJI_SENTIMENT_MAP.items():
            if emoji_char in cleaned:
                cleaned = cleaned.replace(emoji_char, replacement)

        # 8. Normalize whitespace (collapse multiple spaces, preserve single paragraph breaks)
        cleaned = MULTI_SPACE_RE.sub(" ", cleaned)
        cleaned = MULTI_NEWLINE_RE.sub("\n\n", cleaned)
        cleaned = cleaned.strip()

        if not cleaned:
            raise ValueError("Input text contains no valid textual content after preprocessing.")

        return cleaned

    @classmethod
    def prepare_for_transformer(cls, text: str, max_words: int = 350) -> str:
        """
        Prepare text for max 512-token transformer budget.
        For long text, use head+tail combination to avoid losing conclusion/summary.
        """
        cleaned = cls.clean_text(text)
        words = cleaned.split()
        
        if len(words) <= max_words:
            return cleaned

        # Document head (first 200 words) + document tail (last 150 words)
        head_count = int(max_words * 0.6)
        tail_count = max_words - head_count
        
        head = " ".join(words[:head_count])
        tail = " ".join(words[-tail_count:])
        
        return f"{head} ... {tail}"
