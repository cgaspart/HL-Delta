"""
ANSI color codes for colored terminal output
"""


class Colors:
    """ANSI color codes for terminal output"""
    RESET = "\033[0m"
    RED = "\033[91m"     # Error messages
    GREEN = "\033[92m"   # Success messages
    YELLOW = "\033[93m"  # Warnings and important highlights
    BLUE = "\033[94m"    # Info messages
    BOLD = "\033[1m"     # Bold text for headers
