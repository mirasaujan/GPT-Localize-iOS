"""
Module for validating input/output and structure of localization files.
"""

import json
import re
from typing import Dict, List, Any, Tuple

def validate_xcstrings_format(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates that the input data follows the .xcstrings format.
    
    Args:
        data: Dictionary containing the .xcstrings data
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Check top-level structure
    if not isinstance(data, dict):
        errors.append("Root must be a dictionary")
        return False, errors
        
    if "strings" not in data:
        errors.append("Missing required 'strings' key")
        return False, errors
        
    if not isinstance(data["strings"], dict):
        errors.append("'strings' must be a dictionary")
        return False, errors
        
    # Validate each string entry
    for key, value in data["strings"].items():
        if not isinstance(value, dict):
            errors.append(f"String entry '{key}' must be a dictionary")
            continue
            
        if "localizations" not in value:
            errors.append(f"String entry '{key}' missing required 'localizations' key")
            continue
            
        if not isinstance(value["localizations"], dict):
            errors.append(f"'localizations' in string entry '{key}' must be a dictionary")
            continue
            
        # Validate each localization
        for lang, loc_data in value["localizations"].items():
            if not isinstance(loc_data, dict):
                errors.append(f"Localization '{lang}' in string '{key}' must be a dictionary")
                continue
                
            # Check base string unit
            if "stringUnit" in loc_data:
                if not isinstance(loc_data["stringUnit"], dict):
                    errors.append(f"'stringUnit' in string '{key}', language '{lang}' must be a dictionary")
                    continue
                    
                if "value" not in loc_data["stringUnit"]:
                    errors.append(f"Missing required 'value' in stringUnit for string '{key}', language '{lang}'")
                    continue
                    
            # Check variations if present
            if "variations" in loc_data:
                if not isinstance(loc_data["variations"], dict):
                    errors.append(f"'variations' in string '{key}', language '{lang}' must be a dictionary")
                    continue
                    
                for var_key, var_data in loc_data["variations"].items():
                    if not isinstance(var_data, dict):
                        errors.append(f"Variation '{var_key}' in string '{key}', language '{lang}' must be a dictionary")
                        continue
                        
                    if "stringUnit" not in var_data:
                        errors.append(f"Missing required 'stringUnit' in variation '{var_key}' for string '{key}', language '{lang}'")
                        continue
                        
                    if not isinstance(var_data["stringUnit"], dict):
                        errors.append(f"'stringUnit' in variation '{var_key}' for string '{key}', language '{lang}' must be a dictionary")
                        continue
                        
                    if "value" not in var_data["stringUnit"]:
                        errors.append(f"Missing required 'value' in stringUnit for variation '{var_key}' in string '{key}', language '{lang}'")
                        continue
                        
    return len(errors) == 0, errors

def validate_translation_output(source_string: str, translated_string: str) -> Tuple[bool, List[str]]:
    """
    Validates that the translation output preserves important elements from the source.
    
    Args:
        source_string: Original string
        translated_string: Translated string
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Check for empty translation
    if not translated_string:
        errors.append("Translation is empty")
        return False, errors
        
    # Check format specifiers (%d, %s, etc.)
    source_formats = re.findall(r'%[diouxXfeEgGcrs]', source_string)
    translated_formats = re.findall(r'%[diouxXfeEgGcrs]', translated_string)
    
    if len(source_formats) != len(translated_formats):
        errors.append(f"Mismatch in format specifiers: source has {source_formats}, translation has {translated_formats}")
    elif sorted(source_formats) != sorted(translated_formats):
        errors.append(f"Format specifiers don't match: source has {source_formats}, translation has {translated_formats}")
        
    # Check named placeholders (%@)
    source_named = re.findall(r'%@', source_string)
    translated_named = re.findall(r'%@', translated_string)
    
    if len(source_named) != len(translated_named):
        errors.append(f"Mismatch in named placeholders: source has {len(source_named)}, translation has {len(translated_named)}")
        
    # Check iOS string format specifiers (%1$@, %2$d, etc.)
    source_ios = re.findall(r'%\d+\$[@diouxXfeEgGcrs]', source_string)
    translated_ios = re.findall(r'%\d+\$[@diouxXfeEgGcrs]', translated_string)
    
    if len(source_ios) != len(translated_ios):
        errors.append(f"Mismatch in iOS format specifiers: source has {source_ios}, translation has {translated_ios}")
    elif sorted(source_ios) != sorted(translated_ios):
        errors.append(f"iOS format specifiers don't match: source has {source_ios}, translation has {translated_ios}")
        
    return len(errors) == 0, errors

def validate_structure_preservation(source_data: Dict[str, Any], translated_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates that the translated data preserves the structure of the source data.
    
    Args:
        source_data: Original .xcstrings data
        translated_data: Translated .xcstrings data
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Check that all source strings exist in translation
    for key, value in source_data.get("strings", {}).items():
        if key not in translated_data.get("strings", {}):
            errors.append(f"Missing string key '{key}' in translation")
            continue
            
        source_locs = value.get("localizations", {})
        translated_locs = translated_data["strings"][key].get("localizations", {})
        
        # Check that all source languages exist
        for lang in source_locs:
            if lang not in translated_locs:
                errors.append(f"Missing language '{lang}' for string '{key}' in translation")
                continue
                
            source_loc = source_locs[lang]
            translated_loc = translated_locs[lang]
            
            # Check variations match
            source_vars = source_loc.get("variations", {})
            translated_vars = translated_loc.get("variations", {})
            
            for var_key in source_vars:
                if var_key not in translated_vars:
                    errors.append(f"Missing variation '{var_key}' for string '{key}', language '{lang}' in translation")
                    continue
                    
                source_var = source_vars[var_key]
                translated_var = translated_vars[var_key]
                
                # Check variation structure
                if "stringUnit" in source_var and "stringUnit" not in translated_var:
                    errors.append(f"Missing stringUnit in variation '{var_key}' for string '{key}', language '{lang}' in translation")
                    continue
                    
    return len(errors) == 0, errors 