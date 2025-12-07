"""
Code formatting utilities for different programming languages.
"""

import subprocess
from pathlib import Path
from typing import Optional


def format_python(code: str, file_path: Optional[str] = None) -> str:
    """
    Format Python code using black.

    Args:
        code: Python code to format
        file_path: Optional file path for context

    Returns:
        Formatted code
    """
    try:
        result = subprocess.run(
            ["black", "-", "--quiet"],
            input=code.encode(),
            capture_output=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.decode()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return code


def format_typescript(code: str, file_path: Optional[str] = None) -> str:
    """
    Format TypeScript code using prettier.

    Args:
        code: TypeScript code to format
        file_path: Optional file path for context

    Returns:
        Formatted code
    """
    try:
        result = subprocess.run(
            ["prettier", "--parser", "typescript", "--stdin-filepath", "file.ts"],
            input=code.encode(),
            capture_output=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.decode()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return code


def format_go(code: str, file_path: Optional[str] = None) -> str:
    """
    Format Go code using gofmt.

    Args:
        code: Go code to format
        file_path: Optional file path for context

    Returns:
        Formatted code
    """
    try:
        result = subprocess.run(
            ["gofmt"],
            input=code.encode(),
            capture_output=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.decode()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return code


def format_rust(code: str, file_path: Optional[str] = None) -> str:
    """
    Format Rust code using rustfmt.

    Args:
        code: Rust code to format
        file_path: Optional file path for context

    Returns:
        Formatted code
    """
    try:
        result = subprocess.run(
            ["rustfmt", "--emit", "stdout"],
            input=code.encode(),
            capture_output=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.decode()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return code


def format_java(code: str, file_path: Optional[str] = None) -> str:
    """
    Format Java code using google-java-format.

    Args:
        code: Java code to format
        file_path: Optional file path for context

    Returns:
        Formatted code
    """
    try:
        result = subprocess.run(
            ["google-java-format", "-"],
            input=code.encode(),
            capture_output=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.decode()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return code


def format_csharp(code: str, file_path: Optional[str] = None) -> str:
    """
    Format C# code using dotnet-format.

    Args:
        code: C# code to format
        file_path: Optional file path for context

    Returns:
        Formatted code
    """
    # dotnet-format requires a file, so we'll skip auto-formatting for now
    return code


def format_code(language: str, code: str, file_path: Optional[str] = None) -> str:
    """
    Format code for specified language.

    Args:
        language: Programming language
        code: Code to format
        file_path: Optional file path for context

    Returns:
        Formatted code
    """
    formatters = {
        "python": format_python,
        "typescript": format_typescript,
        "go": format_go,
        "rust": format_rust,
        "java": format_java,
        "csharp": format_csharp,
    }

    formatter = formatters.get(language)
    if formatter:
        return formatter(code, file_path)

    return code


def indent(code: str, level: int = 1, indent_size: int = 4) -> str:
    """
    Indent code block.

    Args:
        code: Code to indent
        level: Indentation level
        indent_size: Spaces per indent level

    Returns:
        Indented code
    """
    indent_str = " " * (level * indent_size)
    lines = code.split("\n")
    return "\n".join(f"{indent_str}{line}" if line.strip() else line for line in lines)


def add_header_comment(language: str, description: str) -> str:
    """
    Add file header comment.

    Args:
        language: Programming language
        description: File description

    Returns:
        Header comment
    """
    if language == "python":
        return f'"""\n{description}\n"""\n\n'
    elif language in ["typescript", "javascript", "java", "csharp", "go", "rust"]:
        return f"/**\n * {description}\n */\n\n"
    else:
        return f"// {description}\n\n"


def wrap_comment(language: str, text: str, max_width: int = 80) -> str:
    """
    Wrap comment text to max width.

    Args:
        language: Programming language
        text: Comment text
        max_width: Maximum line width

    Returns:
        Wrapped comment
    """
    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    comment_prefix = {
        "python": "# ",
        "typescript": "// ",
        "go": "// ",
        "rust": "// ",
        "java": "// ",
        "csharp": "// ",
    }.get(language, "// ")

    prefix_length = len(comment_prefix)

    for word in words:
        word_length = len(word) + 1  # +1 for space

        if current_length + word_length > max_width - prefix_length:
            lines.append(comment_prefix + " ".join(current_line))
            current_line = [word]
            current_length = word_length
        else:
            current_line.append(word)
            current_length += word_length

    if current_line:
        lines.append(comment_prefix + " ".join(current_line))

    return "\n".join(lines)
