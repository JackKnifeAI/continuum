"""
Naming convention utilities for different programming languages.

Converts names between different cases (snake_case, camelCase, PascalCase, etc.)
"""

import re


def to_snake_case(name: str) -> str:
    """
    Convert to snake_case.

    Examples:
        getUserById -> get_user_by_id
        GetUserById -> get_user_by_id
        get-user-by-id -> get_user_by_id
    """
    # Replace hyphens with underscores
    name = name.replace("-", "_")

    # Insert underscore before uppercase letters
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)

    return name.lower()


def to_camel_case(name: str) -> str:
    """
    Convert to camelCase.

    Examples:
        get_user_by_id -> getUserById
        GetUserById -> getUserById
        get-user-by-id -> getUserById
    """
    # First convert to snake_case to normalize
    snake = to_snake_case(name)

    # Split on underscores
    parts = snake.split("_")

    # First part lowercase, rest title case
    if not parts:
        return name

    return parts[0].lower() + "".join(word.capitalize() for word in parts[1:] if word)


def to_pascal_case(name: str) -> str:
    """
    Convert to PascalCase.

    Examples:
        get_user_by_id -> GetUserById
        getUserById -> GetUserById
        get-user-by-id -> GetUserById
    """
    # First convert to snake_case to normalize, then convert to PascalCase
    snake = to_snake_case(name)

    # Split on underscores
    parts = snake.split("_")

    # All parts title case
    return "".join(word.capitalize() for word in parts if word)


def to_kebab_case(name: str) -> str:
    """
    Convert to kebab-case.

    Examples:
        getUserById -> get-user-by-id
        GetUserById -> get-user-by-id
        get_user_by_id -> get-user-by-id
    """
    # Replace underscores with hyphens
    name = name.replace("_", "-")

    # Insert hyphen before uppercase letters
    name = re.sub("(.)([A-Z][a-z]+)", r"\1-\2", name)
    name = re.sub("([a-z0-9])([A-Z])", r"\1-\2", name)

    return name.lower()


def to_constant_case(name: str) -> str:
    """
    Convert to CONSTANT_CASE.

    Examples:
        getUserById -> GET_USER_BY_ID
        get_user_by_id -> GET_USER_BY_ID
    """
    return to_snake_case(name).upper()


def get_class_name(language: str, name: str) -> str:
    """
    Get class name for language.

    Args:
        language: Target language
        name: Base name

    Returns:
        Class name following language conventions
    """
    if language in ["python", "ruby"]:
        return to_pascal_case(name)
    elif language in ["typescript", "javascript", "java", "csharp", "go", "rust"]:
        return to_pascal_case(name)
    else:
        return to_pascal_case(name)


def get_method_name(language: str, name: str) -> str:
    """
    Get method name for language.

    Args:
        language: Target language
        name: Base name

    Returns:
        Method name following language conventions
    """
    if language == "python":
        return to_snake_case(name)
    elif language in ["typescript", "javascript", "java"]:
        return to_camel_case(name)
    elif language == "go":
        # Public methods: PascalCase, private: camelCase
        # Default to PascalCase for SDK methods
        return to_pascal_case(name)
    elif language == "rust":
        return to_snake_case(name)
    elif language == "csharp":
        return to_pascal_case(name)
    else:
        return to_camel_case(name)


def get_variable_name(language: str, name: str) -> str:
    """
    Get variable name for language.

    Args:
        language: Target language
        name: Base name

    Returns:
        Variable name following language conventions
    """
    if language in ["python", "ruby", "rust"]:
        return to_snake_case(name)
    elif language in ["typescript", "javascript", "java"]:
        return to_camel_case(name)
    elif language == "go":
        return to_camel_case(name)
    elif language == "csharp":
        return to_camel_case(name)
    else:
        return to_camel_case(name)


def get_constant_name(language: str, name: str) -> str:
    """
    Get constant name for language.

    Args:
        language: Target language
        name: Base name

    Returns:
        Constant name following language conventions
    """
    if language in ["python", "ruby"]:
        return to_constant_case(name)
    elif language in ["typescript", "javascript"]:
        return to_constant_case(name)
    elif language == "java":
        return to_constant_case(name)
    elif language == "go":
        return to_pascal_case(name)
    elif language == "rust":
        return to_constant_case(name)
    elif language == "csharp":
        return to_pascal_case(name)
    else:
        return to_constant_case(name)


def get_file_name(language: str, name: str) -> str:
    """
    Get file name for language.

    Args:
        language: Target language
        name: Base name

    Returns:
        File name following language conventions
    """
    if language in ["python", "ruby"]:
        return to_snake_case(name)
    elif language in ["typescript", "javascript"]:
        return to_kebab_case(name)
    elif language == "java":
        return to_pascal_case(name)  # Java files match class names
    elif language == "go":
        return to_snake_case(name)
    elif language == "rust":
        return to_snake_case(name)
    elif language == "csharp":
        return to_pascal_case(name)  # C# files match class names
    else:
        return to_snake_case(name)


def get_package_name(language: str, name: str) -> str:
    """
    Get package/module name for language.

    Args:
        language: Target language
        name: Base name

    Returns:
        Package name following language conventions
    """
    if language == "python":
        return to_snake_case(name)
    elif language in ["typescript", "javascript"]:
        return to_kebab_case(name)
    elif language == "java":
        return to_snake_case(name).replace("_", "")
    elif language == "go":
        return to_snake_case(name).replace("_", "")
    elif language == "rust":
        return to_snake_case(name)
    elif language == "csharp":
        return to_pascal_case(name)
    else:
        return to_snake_case(name)


def pluralize(word: str) -> str:
    """
    Simple pluralization.

    Args:
        word: Singular word

    Returns:
        Plural form
    """
    if word.endswith("y"):
        return word[:-1] + "ies"
    elif word.endswith("s"):
        return word + "es"
    else:
        return word + "s"


def singularize(word: str) -> str:
    """
    Simple singularization.

    Args:
        word: Plural word

    Returns:
        Singular form
    """
    if word.endswith("ies"):
        return word[:-3] + "y"
    elif word.endswith("ses"):
        return word[:-2]
    elif word.endswith("s"):
        return word[:-1]
    else:
        return word


def sanitize_identifier(language: str, name: str) -> str:
    """
    Sanitize identifier to be valid for language.

    Args:
        language: Target language
        name: Identifier name

    Returns:
        Sanitized identifier
    """
    # Reserved keywords by language
    reserved = {
        "python": {
            "and", "as", "assert", "async", "await", "break", "class", "continue",
            "def", "del", "elif", "else", "except", "finally", "for", "from",
            "global", "if", "import", "in", "is", "lambda", "nonlocal", "not",
            "or", "pass", "raise", "return", "try", "while", "with", "yield"
        },
        "typescript": {
            "break", "case", "catch", "class", "const", "continue", "debugger",
            "default", "delete", "do", "else", "enum", "export", "extends",
            "false", "finally", "for", "function", "if", "import", "in",
            "instanceof", "new", "null", "return", "super", "switch", "this",
            "throw", "true", "try", "typeof", "var", "void", "while", "with"
        },
        "java": {
            "abstract", "assert", "boolean", "break", "byte", "case", "catch",
            "char", "class", "const", "continue", "default", "do", "double",
            "else", "enum", "extends", "final", "finally", "float", "for",
            "goto", "if", "implements", "import", "instanceof", "int",
            "interface", "long", "native", "new", "package", "private",
            "protected", "public", "return", "short", "static", "strictfp",
            "super", "switch", "synchronized", "this", "throw", "throws",
            "transient", "try", "void", "volatile", "while"
        },
        "go": {
            "break", "case", "chan", "const", "continue", "default", "defer",
            "else", "fallthrough", "for", "func", "go", "goto", "if", "import",
            "interface", "map", "package", "range", "return", "select",
            "struct", "switch", "type", "var"
        },
        "rust": {
            "as", "break", "const", "continue", "crate", "else", "enum",
            "extern", "false", "fn", "for", "if", "impl", "in", "let", "loop",
            "match", "mod", "move", "mut", "pub", "ref", "return", "self",
            "Self", "static", "struct", "super", "trait", "true", "type",
            "unsafe", "use", "where", "while"
        },
        "csharp": {
            "abstract", "as", "base", "bool", "break", "byte", "case", "catch",
            "char", "checked", "class", "const", "continue", "decimal",
            "default", "delegate", "do", "double", "else", "enum", "event",
            "explicit", "extern", "false", "finally", "fixed", "float", "for",
            "foreach", "goto", "if", "implicit", "in", "int", "interface",
            "internal", "is", "lock", "long", "namespace", "new", "null",
            "object", "operator", "out", "override", "params", "private",
            "protected", "public", "readonly", "ref", "return", "sbyte",
            "sealed", "short", "sizeof", "stackalloc", "static", "string",
            "struct", "switch", "this", "throw", "true", "try", "typeof",
            "uint", "ulong", "unchecked", "unsafe", "ushort", "using",
            "virtual", "void", "volatile", "while"
        }
    }

    # Check if name is reserved
    keywords = reserved.get(language, set())
    if name.lower() in keywords:
        return f"{name}_"

    return name
