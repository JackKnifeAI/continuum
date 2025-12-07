"""
CONTINUUM SDK Generator

Generates client libraries in multiple languages from OpenAPI specification.
"""

__version__ = "0.3.0"

from .openapi_parser import OpenAPIParser
from .generators.base import BaseSDKGenerator
from .generators.python_gen import PythonGenerator
from .generators.typescript_gen import TypeScriptGenerator
from .generators.go_gen import GoGenerator
from .generators.rust_gen import RustGenerator
from .generators.java_gen import JavaGenerator
from .generators.csharp_gen import CSharpGenerator

__all__ = [
    "OpenAPIParser",
    "BaseSDKGenerator",
    "PythonGenerator",
    "TypeScriptGenerator",
    "GoGenerator",
    "RustGenerator",
    "JavaGenerator",
    "CSharpGenerator",
]

SUPPORTED_LANGUAGES = {
    "python": PythonGenerator,
    "typescript": TypeScriptGenerator,
    "go": GoGenerator,
    "rust": RustGenerator,
    "java": JavaGenerator,
    "csharp": CSharpGenerator,
}


def generate_sdk(language: str, spec_path: str, output_dir: str) -> None:
    """
    Generate SDK for specified language.

    Args:
        language: Target language (python, typescript, go, rust, java, csharp)
        spec_path: Path to OpenAPI specification
        output_dir: Output directory for generated SDK
    """
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language: {language}. "
            f"Supported: {', '.join(SUPPORTED_LANGUAGES.keys())}"
        )

    parser = OpenAPIParser(spec_path)
    spec = parser.parse()

    generator_class = SUPPORTED_LANGUAGES[language]
    generator = generator_class(spec)

    result = generator.generate(output_dir)

    return result
