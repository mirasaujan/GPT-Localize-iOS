"""
Module for processing .xcstrings files and managing translations.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

from . import LocalizationString, TranslationResult

logger = logging.getLogger(__name__)

class XCStringsProcessor:
    """Handles reading and writing of .xcstrings files."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.data: Dict[str, Any] = {}
        self.load_file()

    def load_file(self) -> None:
        """Load and parse the .xcstrings file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            logger.error(f"File not found: {self.file_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in file: {self.file_path}")
            raise

    def save_file(self) -> None:
        """Save the current state back to the .xcstrings file."""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get_strings_for_translation(self, source_lang: str, target_lang: str) -> List[Tuple[LocalizationString, Tuple[str, str, Optional[Tuple[str, str]]]]]:
        """
        Extract strings that need translation from source to target language.
        Returns a list of (LocalizationString, path) tuples.
        """
        logger.debug(f"Looking for strings to translate from {source_lang} to {target_lang}")
        strings = []
        for key, value in self.data.get("strings", {}).items():
            logger.debug(f"Processing key: {key}")
            if not isinstance(value, dict):
                logger.debug(f"Skipping {key}: not a dictionary")
                continue

            # Handle base string
            if source_lang in value.get("localizations", {}):
                source = value["localizations"][source_lang]
                logger.debug(f"Found source localization for {key}: {source}")
                if "stringUnit" not in source:
                    logger.debug(f"Skipping {key}: no stringUnit in source")
                    continue

                source_string = source["stringUnit"]["value"]
                comment = value.get("extractionState", "")

                # Check if translation is needed
                target_data = value.get("localizations", {}).get(target_lang, {})
                if not target_data or target_data.get("stringUnit", {}).get("state") == "new":
                    logger.debug(f"Adding {key} for translation: {source_string}")
                    strings.append((
                        LocalizationString(source_string, comment),
                        (key, target_lang, None)
                    ))
                else:
                    logger.debug(f"Skipping {key}: already translated")

            # Handle variations
            variations = value.get("variations", {})
            for var_key, var_data in variations.items():
                logger.debug(f"Processing variation {var_key} for {key}")
                if not isinstance(var_data, dict):
                    logger.debug(f"Skipping variation {var_key}: not a dictionary")
                    continue

                if source_lang in var_data.get("localizations", {}):
                    source = var_data["localizations"][source_lang]
                    if "stringUnit" not in source:
                        logger.debug(f"Skipping variation {var_key}: no stringUnit in source")
                        continue

                    source_string = source["stringUnit"]["value"]
                    device = var_data.get("device", "")
                    comment = f"{value.get('extractionState', '')} [Variation for {device}]"

                    # Check if translation is needed
                    target_data = var_data.get("localizations", {}).get(target_lang, {})
                    if not target_data or target_data.get("stringUnit", {}).get("state") == "new":
                        logger.debug(f"Adding variation {var_key} for translation: {source_string}")
                        strings.append((
                            LocalizationString(source_string, comment),
                            (key, target_lang, (var_key, device))
                        ))
                    else:
                        logger.debug(f"Skipping variation {var_key}: already translated")

        logger.debug(f"Found {len(strings)} strings to translate")
        return strings

    def update_translations(self, results: List[TranslationResult]) -> None:
        """Update the .xcstrings file with translated strings."""
        for result in results:
            key, lang, variation = result.path
            if key not in self.data.get("strings", {}):
                continue

            if variation:
                var_key, _ = variation
                if var_key not in self.data["strings"][key].get("variations", {}):
                    continue
                
                target_data = self.data["strings"][key]["variations"][var_key].setdefault("localizations", {}).setdefault(lang, {})
            else:
                target_data = self.data["strings"][key].setdefault("localizations", {}).setdefault(lang, {})

            target_data["stringUnit"] = {
                "value": result.translated,
                "state": result.state
            }

        self.save_file()
