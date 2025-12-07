"""
Type mapping utilities for different programming languages.

Maps OpenAPI types to language-native types.
"""

from typing import Dict, Optional


TYPE_MAPS: Dict[str, Dict[str, str]] = {
    "python": {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "array": "List",
        "object": "Dict[str, Any]",
        "null": "None",
        # Formats
        "string:date-time": "datetime",
        "string:date": "date",
        "string:uuid": "UUID",
        "string:email": "str",
        "string:uri": "str",
        "string:password": "str",
        "number:float": "float",
        "number:double": "float",
        "integer:int32": "int",
        "integer:int64": "int",
    },
    "typescript": {
        "string": "string",
        "integer": "number",
        "number": "number",
        "boolean": "boolean",
        "array": "Array",
        "object": "Record<string, any>",
        "null": "null",
        # Formats
        "string:date-time": "Date",
        "string:date": "Date",
        "string:uuid": "string",
        "string:email": "string",
        "string:uri": "string",
        "string:password": "string",
        "number:float": "number",
        "number:double": "number",
        "integer:int32": "number",
        "integer:int64": "number",
    },
    "go": {
        "string": "string",
        "integer": "int",
        "number": "float64",
        "boolean": "bool",
        "array": "[]",
        "object": "map[string]interface{}",
        "null": "nil",
        # Formats
        "string:date-time": "time.Time",
        "string:date": "time.Time",
        "string:uuid": "string",
        "string:email": "string",
        "string:uri": "string",
        "string:password": "string",
        "number:float": "float32",
        "number:double": "float64",
        "integer:int32": "int32",
        "integer:int64": "int64",
    },
    "rust": {
        "string": "String",
        "integer": "i64",
        "number": "f64",
        "boolean": "bool",
        "array": "Vec",
        "object": "HashMap<String, serde_json::Value>",
        "null": "Option",
        # Formats
        "string:date-time": "chrono::DateTime<chrono::Utc>",
        "string:date": "chrono::NaiveDate",
        "string:uuid": "uuid::Uuid",
        "string:email": "String",
        "string:uri": "String",
        "string:password": "String",
        "number:float": "f32",
        "number:double": "f64",
        "integer:int32": "i32",
        "integer:int64": "i64",
    },
    "java": {
        "string": "String",
        "integer": "Integer",
        "number": "Double",
        "boolean": "Boolean",
        "array": "List",
        "object": "Map<String, Object>",
        "null": "null",
        # Formats
        "string:date-time": "OffsetDateTime",
        "string:date": "LocalDate",
        "string:uuid": "UUID",
        "string:email": "String",
        "string:uri": "String",
        "string:password": "String",
        "number:float": "Float",
        "number:double": "Double",
        "integer:int32": "Integer",
        "integer:int64": "Long",
    },
    "csharp": {
        "string": "string",
        "integer": "int",
        "number": "double",
        "boolean": "bool",
        "array": "List",
        "object": "Dictionary<string, object>",
        "null": "null",
        # Formats
        "string:date-time": "DateTimeOffset",
        "string:date": "DateTime",
        "string:uuid": "Guid",
        "string:email": "string",
        "string:uri": "string",
        "string:password": "string",
        "number:float": "float",
        "number:double": "double",
        "integer:int32": "int",
        "integer:int64": "long",
    },
}


IMPORTS_BY_TYPE = {
    "python": {
        "datetime": "from datetime import datetime, date",
        "UUID": "from uuid import UUID",
        "List": "from typing import List",
        "Dict": "from typing import Dict",
        "Any": "from typing import Any",
        "Optional": "from typing import Optional",
    },
    "typescript": {
        # TypeScript doesn't need explicit imports for built-in types
    },
    "go": {
        "time.Time": "time",
        "uuid.UUID": "github.com/google/uuid",
    },
    "rust": {
        "chrono::DateTime": "chrono",
        "uuid::Uuid": "uuid",
        "HashMap": "std::collections::HashMap",
        "Vec": "",  # Built-in
    },
    "java": {
        "OffsetDateTime": "java.time.OffsetDateTime",
        "LocalDate": "java.time.LocalDate",
        "UUID": "java.util.UUID",
        "List": "java.util.List",
        "Map": "java.util.Map",
    },
    "csharp": {
        "DateTimeOffset": "System",
        "DateTime": "System",
        "Guid": "System",
        "List": "System.Collections.Generic",
        "Dictionary": "System.Collections.Generic",
    },
}


def map_type(
    language: str, openapi_type: str, format: Optional[str] = None, nullable: bool = False
) -> str:
    """
    Map OpenAPI type to language-specific type.

    Args:
        language: Target language
        openapi_type: OpenAPI type (string, integer, number, boolean, array, object)
        format: Optional format specifier (uuid, date-time, etc.)
        nullable: Whether the type is nullable

    Returns:
        Language-specific type string
    """
    if language not in TYPE_MAPS:
        raise ValueError(f"Unsupported language: {language}")

    type_map = TYPE_MAPS[language]

    # Try with format first
    if format:
        key = f"{openapi_type}:{format}"
        if key in type_map:
            base_type = type_map[key]
        else:
            base_type = type_map.get(openapi_type, "any")
    else:
        base_type = type_map.get(openapi_type, "any")

    # Handle nullable types
    if nullable:
        if language == "python":
            return f"Optional[{base_type}]"
        elif language == "typescript":
            return f"{base_type} | null"
        elif language == "rust":
            return f"Option<{base_type}>"
        elif language == "csharp":
            return f"{base_type}?"
        # Go and Java handle nullability differently

    return base_type


def get_required_imports(language: str, types_used: set) -> list:
    """
    Get list of required imports for the given types.

    Args:
        language: Target language
        types_used: Set of type names used in the code

    Returns:
        List of import statements
    """
    if language not in IMPORTS_BY_TYPE:
        return []

    imports = set()
    import_map = IMPORTS_BY_TYPE[language]

    for type_name in types_used:
        if type_name in import_map and import_map[type_name]:
            imports.add(import_map[type_name])

    return sorted(imports)


def map_array_type(language: str, item_type: str) -> str:
    """
    Map array type with item type.

    Args:
        language: Target language
        item_type: Type of array items

    Returns:
        Language-specific array type
    """
    if language == "python":
        return f"List[{item_type}]"
    elif language == "typescript":
        return f"Array<{item_type}>"
    elif language == "go":
        return f"[]{item_type}"
    elif language == "rust":
        return f"Vec<{item_type}>"
    elif language == "java":
        return f"List<{item_type}>"
    elif language == "csharp":
        return f"List<{item_type}>"
    else:
        return f"Array<{item_type}>"


def map_dict_type(language: str, value_type: str = "Any") -> str:
    """
    Map dictionary/map type.

    Args:
        language: Target language
        value_type: Type of dictionary values

    Returns:
        Language-specific dictionary type
    """
    if language == "python":
        return f"Dict[str, {value_type}]"
    elif language == "typescript":
        return f"Record<string, {value_type}>"
    elif language == "go":
        return f"map[string]{value_type}"
    elif language == "rust":
        return f"HashMap<String, {value_type}>"
    elif language == "java":
        return f"Map<String, {value_type}>"
    elif language == "csharp":
        return f"Dictionary<string, {value_type}>"
    else:
        return f"Map<string, {value_type}>"


def get_default_value(language: str, openapi_type: str) -> str:
    """
    Get default value for a type.

    Args:
        language: Target language
        openapi_type: OpenAPI type

    Returns:
        Default value as string
    """
    defaults = {
        "python": {
            "string": '""',
            "integer": "0",
            "number": "0.0",
            "boolean": "False",
            "array": "[]",
            "object": "{}",
            "null": "None",
        },
        "typescript": {
            "string": '""',
            "integer": "0",
            "number": "0",
            "boolean": "false",
            "array": "[]",
            "object": "{}",
            "null": "null",
        },
        "go": {
            "string": '""',
            "integer": "0",
            "number": "0.0",
            "boolean": "false",
            "array": "nil",
            "object": "nil",
        },
        "rust": {
            "string": 'String::new()',
            "integer": "0",
            "number": "0.0",
            "boolean": "false",
            "array": "Vec::new()",
            "object": "HashMap::new()",
        },
        "java": {
            "string": '""',
            "integer": "0",
            "number": "0.0",
            "boolean": "false",
            "array": "new ArrayList<>()",
            "object": "new HashMap<>()",
            "null": "null",
        },
        "csharp": {
            "string": '""',
            "integer": "0",
            "number": "0.0",
            "boolean": "false",
            "array": "new List<>()",
            "object": "new Dictionary<>()",
            "null": "null",
        },
    }

    return defaults.get(language, {}).get(openapi_type, "null")
