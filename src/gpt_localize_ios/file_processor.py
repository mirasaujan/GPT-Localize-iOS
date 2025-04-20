"""
Module for processing .xcstrings files and managing translations.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

from . import LocalizationString, TranslationResult, TranslationBatch

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
        logger.debug(f"Total keys in strings: {len(self.data.get('strings', {}))}")
        strings = []
        for key, value in self.data.get("strings", {}).items():
            logger.debug(f"\nProcessing key: {key}")
            if not isinstance(value, dict):
                logger.debug(f"Skipping {key}: not a dictionary")
                continue

            # Get source string from source language localization or key
            localizations = value.get("localizations", {})
            source_localization = localizations.get(source_lang, {})
            
            # If no source localization exists, create it using the key
            if not source_localization or "stringUnit" not in source_localization:
                source_string = key
                # Create source language localization
                self.data["strings"][key].setdefault("localizations", {}).setdefault(source_lang, {})["stringUnit"] = {
                    "value": source_string,
                    "state": "translated"
                }
                logger.debug(f"Created source language localization for {key}")
            else:
                source_string = source_localization["stringUnit"]["value"]
            
            comment = value.get("extractionState", "")
            logger.debug(f"Initial state - key: {key}, source: {source_string}, comment: {comment}")

            # Check if translation is needed
            if target_lang not in localizations:
                logger.debug(f"Adding {key} for translation: {source_string}")
                strings.append((
                    LocalizationString(source_string, comment),
                    (key, target_lang, None)
                ))
            else:
                logger.debug(f"Skipping {key}: already has {target_lang} translation")

            # Handle variations
            variations = value.get("variations", {})
            if variations:
                logger.debug(f"Processing variations for {key}: {list(variations.keys())}")
                for var_key, var_data in variations.items():
                    logger.debug(f"\nProcessing variation {var_key} for {key}")
                    if not isinstance(var_data, dict):
                        logger.debug(f"Skipping variation {var_key}: not a dictionary")
                        continue

                    # Get source string from the source language variation or create it
                    var_localizations = var_data.get("localizations", {})
                    var_source = var_localizations.get(source_lang, {})
                    
                    if not var_source or "stringUnit" not in var_source:
                        # For variations, use the stringUnit value if available, otherwise use key
                        source_string = var_data.get("stringUnit", {}).get("value", key)
                        # Create source language localization for variation
                        self.data["strings"][key]["variations"][var_key].setdefault("localizations", {}).setdefault(source_lang, {})["stringUnit"] = {
                            "value": source_string,
                            "state": "translated"
                        }
                        logger.debug(f"Created source language localization for variation {var_key}")
                    else:
                        source_string = var_source["stringUnit"]["value"]
                    
                    device = var_data.get("device", "")
                    comment = f"{value.get('extractionState', '')} [Variation for {device}]"
                    logger.debug(f"Found variation source string: {source_string}")

                    # Check if translation is needed
                    if target_lang not in var_localizations:
                        logger.debug(f"Adding variation {var_key} for translation: {source_string}")
                        strings.append((
                            LocalizationString(source_string, comment),
                            (key, target_lang, (var_key, device))
                        ))
                    else:
                        logger.debug(f"Skipping variation {var_key}: already has {target_lang} translation")

        # Save the file to persist any new source language localizations
        self.save_file()

        logger.debug(f"\nFound {len(strings)} strings to translate")
        if strings:
            logger.debug("Strings to translate:")
            for string, (key, lang, var) in strings:
                logger.debug(f"- {key}: {string.value}")
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

    def get_strings_for_translation_chunked(self, source_lang: str, target_lang: str, chunk_size: int = 30) -> List[TranslationBatch]:
        """
        Extract strings that need translation and break them into chunks based on word count.
        
        Args:
            source_lang: Source language code
            target_lang: Target language code
            chunk_size: Maximum number of words per chunk
            
        Returns:
            List of TranslationBatch objects
        """
        all_strings = self.get_strings_for_translation(source_lang, target_lang)
        
        # Initialize chunk tracking
        current_chunk_strings = []
        current_chunk_paths = []
        current_word_count = 0
        chunks = []
        
        for string, path in all_strings:
            words = len(string.value.split())
            
            if current_word_count + words > chunk_size:
                # Create new batch
                chunks.append(TranslationBatch(
                    strings=current_chunk_strings,
                    paths=current_chunk_paths,
                    source_lang=source_lang,
                    target_lang=target_lang
                ))
                current_chunk_strings = []
                current_chunk_paths = []
                current_word_count = 0
                
            current_chunk_strings.append(string)
            current_chunk_paths.append(path)
            current_word_count += words
        
        # Add remaining strings
        if current_chunk_strings:
            chunks.append(TranslationBatch(
                strings=current_chunk_strings,
                paths=current_chunk_paths,
                source_lang=source_lang,
                target_lang=target_lang
            ))
        
        # Update chunk metadata
        for i, chunk in enumerate(chunks):
            chunk.chunk_index = i
            chunk.total_chunks = len(chunks)
        
        return chunks
