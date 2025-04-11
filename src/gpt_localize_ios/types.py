"""
Type definitions for iOS localization handling.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path

# Constants
DEFAULT_MODEL = "gpt-4-turbo-preview"
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