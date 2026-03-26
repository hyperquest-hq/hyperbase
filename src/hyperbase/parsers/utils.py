from typing import List


def filter_alphanumeric_strings(strings: List[str]) -> List[str]:
    """
    Filter a list of strings to include only those containing alphanumeric characters,
    and remove all non-alphanumeric characters from each string.

    Args:
        strings: List of strings to filter

    Returns:
        Filtered list containing only lowercased alphanumeric characters
    """
    filtered = []
    for s in strings:
        # Remove non-alphanumeric characters and lowercase
        cleaned = ''.join(c.lower() for c in s if c.isalnum())
        # Only include if result is non-empty
        if cleaned:
            filtered.append(cleaned)
    return filtered
