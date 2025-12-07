"""
Base SDK generator.

All language-specific generators inherit from this base.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from ..openapi_parser import OpenAPISpec, Schema, Endpoint
from ..utils import format_code


@dataclass
class GenerationResult:
    """Result of SDK generation"""

    language: str
    output_dir: Path
    files_created: List[Path]
    success: bool
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class BaseSDKGenerator(ABC):
    """Base class for SDK generators"""

    def __init__(self, spec: OpenAPISpec):
        self.spec = spec
        self.output_dir: Optional[Path] = None

    @abstractmethod
    def get_language(self) -> str:
        """Return language name"""
        pass

    @abstractmethod
    def generate(self, output_dir: str) -> GenerationResult:
        """
        Generate complete SDK.

        Args:
            output_dir: Directory to output generated files

        Returns:
            GenerationResult with details
        """
        pass

    @abstractmethod
    def generate_models(self) -> List[Path]:
        """Generate model/schema classes"""
        pass

    @abstractmethod
    def generate_client(self) -> Path:
        """Generate main client class"""
        pass

    @abstractmethod
    def generate_resources(self) -> List[Path]:
        """Generate resource classes (grouped endpoints)"""
        pass

    @abstractmethod
    def generate_auth(self) -> Path:
        """Generate authentication handling"""
        pass

    @abstractmethod
    def generate_errors(self) -> Path:
        """Generate error classes"""
        pass

    @abstractmethod
    def generate_utils(self) -> List[Path]:
        """Generate utility functions"""
        pass

    @abstractmethod
    def generate_tests(self) -> List[Path]:
        """Generate test files"""
        pass

    @abstractmethod
    def generate_docs(self) -> List[Path]:
        """Generate documentation files"""
        pass

    @abstractmethod
    def generate_package_files(self) -> List[Path]:
        """Generate package configuration (setup.py, package.json, etc.)"""
        pass

    def write_file(self, file_path: Path, content: str, format: bool = True) -> Path:
        """
        Write content to file with formatting.

        Args:
            file_path: Path to write
            content: File content
            format: Whether to format the code

        Returns:
            Path to created file
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if format:
            content = format_code(self.get_language(), content, str(file_path))

        with open(file_path, "w") as f:
            f.write(content)

        return file_path

    def group_endpoints_by_tag(self) -> Dict[str, List[Endpoint]]:
        """
        Group endpoints by tag.

        Returns:
            Dict mapping tag name to list of endpoints
        """
        grouped: Dict[str, List[Endpoint]] = {}

        for endpoint in self.spec.endpoints:
            # Use first tag or "default"
            tag = endpoint.tags[0] if endpoint.tags else "default"

            if tag not in grouped:
                grouped[tag] = []

            grouped[tag].append(endpoint)

        return grouped

    def get_schema_by_ref(self, ref: str) -> Optional[Schema]:
        """
        Get schema by $ref pointer.

        Args:
            ref: Reference like #/components/schemas/Memory

        Returns:
            Schema if found
        """
        if not ref or not ref.startswith("#/components/schemas/"):
            return None

        schema_name = ref.split("/")[-1]
        return self.spec.schemas.get(schema_name)

    def resolve_schema_type(self, schema_data: Dict[str, Any]) -> str:
        """
        Resolve schema type, following $ref if present.

        Args:
            schema_data: Schema definition

        Returns:
            Type name
        """
        if "$ref" in schema_data:
            return schema_data["$ref"].split("/")[-1]
        else:
            return schema_data.get("type", "object")

    def get_endpoint_function_name(self, endpoint: Endpoint) -> str:
        """
        Get function name for endpoint.

        Args:
            endpoint: Endpoint definition

        Returns:
            Function name
        """
        # Use operationId if available
        if endpoint.operation_id:
            name = endpoint.operation_id
        else:
            # Generate from method and path
            path_parts = [p for p in endpoint.path.split("/") if p and not p.startswith("{")]
            name = f"{endpoint.method.lower()}_{'_'.join(path_parts)}"

        return name

    def extract_path_parameters(self, path: str) -> List[str]:
        """
        Extract parameter names from path.

        Args:
            path: API path like /memories/{memory_id}

        Returns:
            List of parameter names
        """
        import re

        matches = re.findall(r"\{([^}]+)\}", path)
        return matches

    def get_success_response(self, endpoint: Endpoint) -> Optional[Any]:
        """
        Get success response schema for endpoint.

        Args:
            endpoint: Endpoint definition

        Returns:
            Response schema if found
        """
        for response in endpoint.responses:
            if response.status_code.startswith("2"):  # 2xx success
                return response

        return None
