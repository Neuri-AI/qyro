import re

def to_camel_case(app_name: str) -> str:
    """
        Converts a given string to CamelCase format.

        Args:
            app_name (str): The input string to be converted.

        Returns:
            str: The converted string in CamelCase format.
    """
    if app_name == ".":
        return "."

    cleaned = re.sub(r'[-_ ]+', ' ', app_name.strip())

    parts = cleaned.split()
    if len(parts) == 1:
        parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?![a-z])', parts[0])

    return ''.join(word.capitalize() for word in parts)