"""
Parser module for handling .xcstrings files.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

from .types import LocalizationString, TranslationResult

class XCStringsParser:
    """Parser for iOS .xcstrings localization files."""
    
    @staticmethod
    def read_file(file_path: Path) -> Dict:
        """Read and parse an .xcstrings file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def write_file(file_path: Path, content: Dict) -> None:
        """Write content to an .xcstrings file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)

    @staticmethod
    def extract_strings(content: Dict, source_lang: str) -> List[Tuple[str, LocalizationString]]:
        """Extract localizable strings from parsed content."""
        strings = []
        for key, data in content.get("strings", {}).items():
            if not isinstance(data, dict) or "extractionState" not in data:
                continue

            localization = data.get("localizations", {}).get(source_lang, {})
            if not localization:
                continue

            string = LocalizationString(
                value=localization.get("stringUnit", {}).get("value", ""),
                comment=data.get("comment"),
                variations=localization.get("variations", {})
            )
            strings.append((key, string))
        return strings

    @staticmethod
    def update_translations(content: Dict, results: List[TranslationResult], target_lang: str) -> Dict:
        """Update content with translated strings."""
        for result in results:
            if result.state == "error":
                continue

            string_data = content["strings"].get(result.path, {})
            if not string_data:
                continue

            localizations = string_data.setdefault("localizations", {})
            target_loc = localizations.setdefault(target_lang, {})
            
            # Create or update the stringUnit
            target_loc["stringUnit"] = {"value": result.translated, "state": result.state}

        return content 