"""
Module for handling translations using OpenAI's GPT models.
"""

import json
import logging
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI

from . import (
    LocalizationString,
    TranslationResult,
    TranslationBatch,
    DEFAULT_MODEL,
    COST_PER_1K_TOKENS
)

logger = logging.getLogger(__name__)

class Translator:
    """Handles translation of strings using OpenAI's GPT models."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.total_tokens = 0
        self.total_cost = 0.0

    def _create_translation_prompt(self, strings: List[LocalizationString], target_lang: str) -> str:
        """Create a prompt for translating multiple strings."""
        strings_json = json.dumps([s.to_dict() for s in strings], ensure_ascii=False, indent=2)
        return f"""Translate the following iOS localization strings to {target_lang}. 
Each string is provided with its value and optional comment for context.
Maintain any format specifiers (like %@, %d) and HTML tags exactly as they appear.
Preserve any whitespace at the start or end of strings.
Return a JSON object with a 'translations' array containing the translated strings.

Input strings:
{strings_json}

Respond with translations in this exact format:
{{
  "translations": [
    "translation1",
    "translation2",
    ...
  ]
}}"""

    def translate_batch(self, batch: TranslationBatch) -> List[TranslationResult]:
        """Translate a batch of strings to the target language."""
        logger.debug(f"Translating batch of {len(batch.strings)} strings to {batch.target_lang}")
        logger.debug(f"Input strings: {[s.value for s in batch.strings]}")
        
        prompt = self._create_translation_prompt(batch.strings, batch.target_lang)
        logger.debug(f"Generated prompt:\n{prompt}")
        
        try:
            logger.debug("Sending request to OpenAI API...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            logger.debug(f"Received response from OpenAI API: {response.choices[0].message.content}")
            
            # Update token usage and cost
            self.total_tokens += response.usage.total_tokens
            self.total_cost += (response.usage.total_tokens / 1000.0) * COST_PER_1K_TOKENS
            logger.debug(f"Token usage: {response.usage.total_tokens}, Cost: ${self.total_cost:.4f}")

            # Parse the response
            content = response.choices[0].message.content
            response_data = json.loads(content)
            translations = response_data.get("translations", [])
            logger.debug(f"Parsed translations: {translations}")

            if len(translations) != len(batch.strings):
                logger.error(f"Translation count mismatch. Expected: {len(batch.strings)}, Got: {len(translations)}")
                logger.error(f"Original strings: {[s.value for s in batch.strings]}")
                logger.error(f"Received translations: {translations}")
                raise ValueError(f"Expected {len(batch.strings)} translations, got {len(translations)}")

            # Create translation results
            results = []
            for string, translation, path in zip(batch.strings, translations, batch.paths):
                logger.debug(f"Creating translation result for '{string.value}' -> '{translation}'")
                results.append(TranslationResult(
                    original=string.value,
                    translated=translation,
                    path=path,
                    state="translated"
                ))

            return results

        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            logger.error(f"Full error: {repr(e)}")
            raise

    def translate_batch_with_retry(self, batch: TranslationBatch, max_retries: int = 3) -> List[TranslationResult]:
        """
        Translate a batch with retry logic for failed strings.
        
        Args:
            batch: The batch of strings to translate
            max_retries: Maximum number of retry attempts for failed strings
            
        Returns:
            List of TranslationResult objects
        """
        retries = 0
        failed_strings = []
        results = []
        
        while retries < max_retries and (retries == 0 or failed_strings):
            try:
                if retries == 0:
                    current_batch = batch
                else:
                    # Create new batch with just failed strings
                    current_batch = TranslationBatch(
                        strings=[s for s, p in zip(batch.strings, batch.paths) if p in failed_strings],
                        paths=failed_strings,
                        source_lang=batch.source_lang,
                        target_lang=batch.target_lang,
                        chunk_index=batch.chunk_index,
                        total_chunks=batch.total_chunks
                    )
                
                batch_results = self.translate_batch(current_batch)
                
                # Filter out any previously failed strings that succeeded
                if retries > 0:
                    results = [r for r in results if r.path not in [br.path for br in batch_results]]
                
                results.extend(batch_results)
                
                # Update failed strings
                failed_strings = [r.path for r in batch_results if r.state == "error"]
                
                if not failed_strings:
                    break
                    
                retries += 1
                logger.warning(f"Retry {retries}/{max_retries} for {len(failed_strings)} failed strings")
                
            except Exception as e:
                logger.error(f"Batch translation error: {str(e)}")
                retries += 1
                if retries == max_retries:
                    raise
        
        return results

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get the current usage statistics."""
        return {
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost, 4)
        } 