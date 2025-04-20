import argparse
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
import sys

from . import Translator, XCStringsProcessor, TranslationProgress
from .validation import validate_translation_counts

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_api_key() -> str:
    """
    Load OpenAI API key from environment with proper error handling.
    Checks multiple locations in order:
    1. Current environment variable
    2. .env file in current directory
    3. .env file in parent directory
    """
    # Try loading from environment first
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key
        
    # List of potential .env file locations
    env_locations = [
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        Path(__file__).parent.parent.parent / ".env"
    ]
    
    # Try each location
    for env_path in env_locations:
        if env_path.exists():
            logger.debug(f"Found .env file at {env_path}")
            load_dotenv(env_path)
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                return api_key
                
    raise ValueError(
        "OPENAI_API_KEY not found. Please either:\n"
        "1. Set OPENAI_API_KEY environment variable\n"
        "2. Create a .env file with OPENAI_API_KEY=your-key\n"
        "3. Export OPENAI_API_KEY=your-key in your shell"
    )

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Translate iOS .xcstrings files using OpenAI GPT")
    parser.add_argument("--input-file", required=True, help="Input .xcstrings file to translate")
    parser.add_argument("--target-language-code", required=True, help="Target language code (e.g., 'de', 'fr')")
    parser.add_argument("--source-language-code", required=True, help="Source language code (e.g., 'en')")
    parser.add_argument("--app-context-path", default="app_context.txt", help="Path to app context file")
    parser.add_argument("--chunk-size", type=int, default=30, help="Maximum words per translation chunk")
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum retry attempts for failed translations")
    args = parser.parse_args()

    try:
        # Load API key with better error handling
        api_key = load_api_key()
        
        # Initialize processor and translator
        processor = XCStringsProcessor(args.input_file)
        translator = Translator(api_key)

        # Get chunked batches
        batches = processor.get_strings_for_translation_chunked(
            args.source_language_code,
            args.target_language_code,
            chunk_size=args.chunk_size
        )

        if not batches:
            logger.info("No strings need translation")
            return 0

        # Initialize progress tracking
        progress = TranslationProgress(
            total_chunks=len(batches),
            completed_chunks=0,
            total_strings=sum(len(batch.strings) for batch in batches),
            completed_strings=0,
            failed_strings=[]
        )

        # Process each batch
        all_results = []
        for batch in batches:
            logger.info(f"Processing chunk {batch.chunk_index + 1}/{batch.total_chunks}")
            
            try:
                results = translator.translate_batch_with_retry(
                    batch,
                    max_retries=args.max_retries
                )
                all_results.extend(results)
                
                # Update progress
                progress.completed_chunks += 1
                progress.completed_strings += len([r for r in results if r.state != "error"])
                progress.failed_strings.extend([r.path for r in results if r.state == "error"])
                
                # Update file after each chunk
                processor.update_translations(results)
                
                # Log progress
                progress_data = progress.to_dict()
                logger.info(f"Progress: {progress_data['progress']}, Strings: {progress_data['strings']}")
                if progress_data['failed']:
                    logger.warning(f"Failed strings: {progress_data['failed']}")
                
            except Exception as e:
                logger.error(f"Error processing chunk {batch.chunk_index + 1}: {str(e)}")
                continue

        # Show final stats
        stats = translator.get_usage_stats()
        logger.info(
            f"Translation completed:\n"
            f"- Chunks: {progress.completed_chunks}/{progress.total_chunks}\n"
            f"- Strings: {progress.completed_strings}/{progress.total_strings}\n"
            f"- Failed: {len(progress.failed_strings)}\n"
            f"- Tokens: {stats['total_tokens']}\n"
            f"- Cost: ${stats['total_cost_usd']}"
        )
        
        if progress.failed_strings:
            logger.warning("Failed strings:")
            for path in progress.failed_strings:
                logger.warning(f"- {path}")
        
        # Save translations
        processor.update_translations(all_results)
        logger.info("Translations saved successfully")
        
        # Validate final translation counts
        is_complete, stats = validate_translation_counts(processor.data, args.source_language_code, args.target_language_code)
        logger.info(f"Translation stats: {stats}")
        if not is_complete:
            logger.warning("Some translations are missing or incomplete")
        
        return 0

    except ValueError as ve:
        logger.error(str(ve))
        return 1
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
