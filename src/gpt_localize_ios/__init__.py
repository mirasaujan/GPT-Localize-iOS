"""
GPT-Localize-iOS: A tool to automatically translate iOS .xcstrings files using GPT-4
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple

# Constants
COST_PER_1K_TOKENS = 0.01  # $0.01 per 1k tokens
DEFAULT_MODEL = "gpt-4o-mini"  # Default model

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
    chunk_index: int = 0  # Track which chunk this is
    total_chunks: int = 1  # Total number of chunks

@dataclass
class TranslationProgress:
    """Tracks progress of translation chunks."""
    total_chunks: int
    completed_chunks: int
    total_strings: int
    completed_strings: int
    failed_strings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "progress": f"{self.completed_chunks}/{self.total_chunks} chunks",
            "strings": f"{self.completed_strings}/{self.total_strings}",
            "failed": len(self.failed_strings),
            "failed_strings": self.failed_strings
        }

# Import and expose main classes
from .translator import Translator
from .file_processor import XCStringsProcessor

__all__ = [
    'Translator',
    'XCStringsProcessor',
    'LocalizationString',
    'TranslationResult',
    'TranslationBatch',
    'TranslationProgress',
    'LANGUAGE_NAMES',
    'DEFAULT_MODEL',
    'COST_PER_1K_TOKENS',
]
