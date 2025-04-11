import argparse
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

from . import Translator, XCStringsProcessor

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Translate iOS .xcstrings files using OpenAI GPT")
    parser.add_argument("--input-file", required=True, help="Input .xcstrings file to translate")
    parser.add_argument("--target-language-code", required=True, help="Target language code (e.g., 'de', 'fr')")
    parser.add_argument("--source-language-code", required=True, help="Source language code (e.g., 'en')")
    parser.add_argument("--app-context-path", default="app_context.txt", help="Path to app context file")
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        return 1

    try:
        # Initialize processor and translator
        processor = XCStringsProcessor(args.input_file)
        translator = Translator(api_key)

        # Get strings that need translation
        strings_to_translate = processor.get_strings_for_translation(
            args.source_language_code,
            args.target_language_code
        )

        if not strings_to_translate:
            logger.info("No strings need translation")
            return 0

        # Translate strings
        from .types import TranslationBatch
        batch = TranslationBatch(
            strings=[s[0] for s in strings_to_translate],
            paths=[s[1] for s in strings_to_translate],
            target_lang=args.target_language_code,
            source_lang=args.source_language_code
        )
        
        results = translator.translate_batch(batch)

        # Update the file with translations
        processor.update_translations(results)

        # Show usage statistics
        stats = translator.get_usage_stats()
        logger.info(f"Translation completed. Tokens used: {stats['total_tokens']}, Cost: ${stats['total_cost_usd']}")
        return 0

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
