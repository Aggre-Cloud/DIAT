"""
Classification and tagging module
Responsible for classifying requirements, marking special requirements, and identifying product associations
"""
import re
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Lazy load config
def get_config():
    """Get classification config"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("config", "007_config/config.py")
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    return config


def categorize_requirement(text):
    """
    Classify a requirement

    Args:
        text: Requirement text

    Returns:
        str: Category name
    """
    config = get_config()
    text_lower = text.lower()
    for category, keywords in config.CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category
    return ''


def is_special_requirement(text):
    """
    Determine if it is a special requirement

    Args:
        text: Requirement text

    Returns:
        bool: Whether it is a special requirement
    """
    config = get_config()
    text_lower = text.lower()
    for keyword in config.SPECIAL_KEYWORDS:
        if keyword in text_lower:
            return True
    return False


def is_product_related(text):
    """
    Determine if it is related to other products

    Args:
        text: Requirement text

    Returns:
        bool: Whether it is product related
    """
    config = get_config()
    text_lower = text.lower()
    for keyword in config.PRODUCT_KEYWORDS:
        if keyword in text_lower:
            return True
    return False


def analyze_requirement(text):
    """
    Analyze a requirement comprehensively, returning classification, special marking, and product association info

    Args:
        text: Requirement text

    Returns:
        dict: Analysis result {
            'category': category,
            'is_special': is special requirement,
            'is_product_related': is product related
        }
    """
    return {
        'category': categorize_requirement(text),
        'is_special': is_special_requirement(text),
        'is_product_related': is_product_related(text)
    }


def batch_analyze(requirements):
    """
    Analyze a batch of requirements

    Args:
        requirements: List of requirement texts

    Returns:
        list: List of analysis results
    """
    results = []
    for req_text in requirements:
        analysis = analyze_requirement(req_text)
        analysis['original_text'] = req_text
        results.append(analysis)
    return results
