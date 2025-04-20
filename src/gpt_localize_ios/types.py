"""
Type definitions for iOS localization handling.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from pathlib import Path

# Constants
DEFAULT_MODEL = "gpt-4o-mini"
COST_PER_1K_TOKENS = 0.01  # Cost in USD per 1K tokens

@dataclass
class LocalizationString:
    """Represents a localizable string from an .xcstrings file."""
    value: str
    comment: Optional[str] = None
    variations: Dict[str, str] = None

    def to_dict(self) -> Dict:
        """Convert to a dictionary format suitable for prompts."""
        return {
            "value": self.value,
            "comment": self.comment if self.comment else "",
            "variations": self.variations if self.variations else {}
        }

@dataclass
class TranslationResult:
    """Represents a translated string with its metadata."""
    original: str
    translated: str
    path: str
    state: str  # "translated", "needs_review", "error"
    error: Optional[str] = None

@dataclass
class TranslationBatch:
    """A batch of strings to be translated together."""
    strings: List[LocalizationString]
    paths: List[str]
    source_lang: str
    target_lang: str
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