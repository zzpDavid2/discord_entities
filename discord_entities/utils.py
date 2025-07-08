def shorten_str(text: str, max_length: int = 1900) -> str:
    """
    Shorten a string to fit within Discord's message length limit.
    
    Args:
        text: The text to shorten
        max_length: Maximum length (default 1900 to leave room for formatting)
        
    Returns:
        Shortened text with " [...]" suffix if truncated
    """
    if len(text) <= max_length:
        return text
    
    # Leave room for " [...]" suffix
    suffix = " [...]"
    available_length = max_length - len(suffix)
    
    # Truncate and add suffix
    return text[:available_length] + suffix 