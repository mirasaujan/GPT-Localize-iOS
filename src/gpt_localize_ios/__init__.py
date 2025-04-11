"""
GPT-Localize-iOS: A tool to automatically translate iOS .xcstrings files using GPT-4
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple

# Constants
COST_PER_1K_TOKENS = 0.01  # $0.01 per 1k tokens
DEFAULT_MODEL = "gpt-4-turbo-preview"  # Default model

LANGUAGE_NAMES = {
    "en": "English",
    "de": "German",
    "es": "Spanish",
    "fr": "French",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "pt": "Portuguese",
    "zh": "Chinese",
    "ar": "Arabic",
    "cs": "Czech",
    "da": "Danish",
    "fi": "Finnish",
    "el": "Greek",
    "hi": "Hindi",
    "hu": "Hungarian",
}

@dataclass
class LocalizationString:
    """Represents a string to be localized with its context."""
    value: str
    comment: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for API requests."""
        return {
            "value": self.value,
            "comment": self.comment,
        }

@dataclass
class TranslationResult:
    """Represents a translated string with its metadata."""
    original: str
    translated: str
    path: Tuple[str, str, Optional[Tuple[str, str]]]  # (key, lang, (variation_key, device) or None)
    state: str = "translated"

@dataclass
class TranslationBatch:
    """Represents a batch of strings to be translated."""
    strings: List[LocalizationString]
    paths: List[Tuple[str, str, Optional[Tuple[str, str]]]]
    target_lang: str
    source_lang: str

# Import and expose main classes
from .translator import Translator
from .file_processor import XCStringsProcessor

__all__ = [
    'Translator',
    'XCStringsProcessor',
    'LocalizationString',
    'TranslationResult',
    'TranslationBatch',
    'LANGUAGE_NAMES',
    'DEFAULT_MODEL',
    'COST_PER_1K_TOKENS',
]
