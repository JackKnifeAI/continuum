"""
OpenAPI specification parser.

Parses OpenAPI 3.1 YAML/JSON specs into structured Python objects.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path
import yaml
import json


@dataclass
class Parameter:
    """API parameter"""

    name: str
    location: str  # path, query, header, cookie
    required: bool = False
    schema_type: str = "string"
    description: str = ""
    default: Any = None
    enum: Optional[List[str]] = None


@dataclass
class RequestBody:
    """API request body"""

    required: bool = True
    content_type: str = "application/json"
    schema_ref: Optional[str] = None
    schema: Optional[Dict[str, Any]] = None


@dataclass
class Response:
    """API response"""

    status_code: str
    description: str
    content_type: str = "application/json"
    schema_ref: Optional[str] = None
    schema: Optional[Dict[str, Any]] = None


@dataclass
class Endpoint:
    """API endpoint"""

    path: str
    method: str
    operation_id: str
    summary: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    parameters: List[Parameter] = field(default_factory=list)
    request_body: Optional[RequestBody] = None
    responses: List[Response] = field(default_factory=list)
    security: Optional[List[Dict[str, List[str]]]] = None


@dataclass
class Schema:
    """Schema definition"""

    name: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    required: List[str] = field(default_factory=list)
    description: str = ""
    example: Optional[Dict[str, Any]] = None
    enum: Optional[List[str]] = None


@dataclass
class SecurityScheme:
    """Security scheme definition"""

    name: str
    type: str  # apiKey, http, oauth2, openIdConnect
    scheme: Optional[str] = None  # For http: bearer, basic, etc.
    bearer_format: Optional[str] = None
    in_location: Optional[str] = None  # For apiKey: header, query, cookie
    header_name: Optional[str] = None


@dataclass
class OpenAPISpec:
    """Parsed OpenAPI specification"""

    version: str
    title: str
    description: str
    api_version: str
    servers: List[Dict[str, str]] = field(default_factory=list)
    endpoints: List[Endpoint] = field(default_factory=list)
    schemas: Dict[str, Schema] = field(default_factory=dict)
    security_schemes: Dict[str, SecurityScheme] = field(default_factory=dict)
    tags: List[Dict[str, str]] = field(default_factory=list)


class OpenAPIParser:
    """Parse OpenAPI specifications"""

    def __init__(self, spec_path: str):
        self.spec_path = Path(spec_path)
        self.raw_spec: Dict[str, Any] = {}

    def parse(self) -> OpenAPISpec:
        """Parse OpenAPI spec file"""
        self._load_spec()

        spec = OpenAPISpec(
            version=self.raw_spec.get("openapi", "3.1.0"),
            title=self.raw_spec["info"]["title"],
            description=self.raw_spec["info"].get("description", ""),
            api_version=self.raw_spec["info"]["version"],
            servers=self.raw_spec.get("servers", []),
            tags=self.raw_spec.get("tags", []),
        )

        # Parse security schemes
        components = self.raw_spec.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        for name, scheme_data in security_schemes.items():
            spec.security_schemes[name] = self._parse_security_scheme(
                name, scheme_data
            )

        # Parse schemas
        schemas = components.get("schemas", {})
        for schema_name, schema_data in schemas.items():
            spec.schemas[schema_name] = self._parse_schema(schema_name, schema_data)

        # Parse endpoints
        paths = self.raw_spec.get("paths", {})
        for path, path_data in paths.items():
            for method, operation_data in path_data.items():
                if method.upper() in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                    endpoint = self._parse_endpoint(path, method, operation_data)
                    spec.endpoints.append(endpoint)

        return spec

    def _load_spec(self) -> None:
        """Load spec from file"""
        if not self.spec_path.exists():
            raise FileNotFoundError(f"Spec file not found: {self.spec_path}")

        with open(self.spec_path, "r") as f:
            if self.spec_path.suffix in [".yaml", ".yml"]:
                self.raw_spec = yaml.safe_load(f)
            elif self.spec_path.suffix == ".json":
                self.raw_spec = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {self.spec_path.suffix}")

    def _parse_security_scheme(
        self, name: str, data: Dict[str, Any]
    ) -> SecurityScheme:
        """Parse security scheme"""
        return SecurityScheme(
            name=name,
            type=data["type"],
            scheme=data.get("scheme"),
            bearer_format=data.get("bearerFormat"),
            in_location=data.get("in"),
            header_name=data.get("name"),
        )

    def _parse_schema(self, name: str, data: Dict[str, Any]) -> Schema:
        """Parse schema definition"""
        return Schema(
            name=name,
            type=data.get("type", "object"),
            properties=data.get("properties", {}),
            required=data.get("required", []),
            description=data.get("description", ""),
            example=data.get("example"),
            enum=data.get("enum"),
        )

    def _parse_endpoint(
        self, path: str, method: str, data: Dict[str, Any]
    ) -> Endpoint:
        """Parse endpoint definition"""
        endpoint = Endpoint(
            path=path,
            method=method.upper(),
            operation_id=data.get("operationId", f"{method}_{path.replace('/', '_')}"),
            summary=data.get("summary", ""),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            security=data.get("security"),
        )

        # Parse parameters
        for param_data in data.get("parameters", []):
            endpoint.parameters.append(self._parse_parameter(param_data))

        # Parse request body
        if "requestBody" in data:
            endpoint.request_body = self._parse_request_body(data["requestBody"])

        # Parse responses
        for status_code, response_data in data.get("responses", {}).items():
            endpoint.responses.append(
                self._parse_response(status_code, response_data)
            )

        return endpoint

    def _parse_parameter(self, data: Dict[str, Any]) -> Parameter:
        """Parse parameter definition"""
        schema = data.get("schema", {})

        return Parameter(
            name=data["name"],
            location=data["in"],
            required=data.get("required", False),
            schema_type=schema.get("type", "string"),
            description=data.get("description", ""),
            default=schema.get("default"),
            enum=schema.get("enum"),
        )

    def _parse_request_body(self, data: Dict[str, Any]) -> RequestBody:
        """Parse request body definition"""
        content = data.get("content", {})
        content_type = list(content.keys())[0] if content else "application/json"
        content_data = content.get(content_type, {})
        schema = content_data.get("schema", {})

        return RequestBody(
            required=data.get("required", True),
            content_type=content_type,
            schema_ref=schema.get("$ref"),
            schema=schema if "$ref" not in schema else None,
        )

    def _parse_response(self, status_code: str, data: Dict[str, Any]) -> Response:
        """Parse response definition"""
        content = data.get("content", {})
        content_type = list(content.keys())[0] if content else "application/json"
        content_data = content.get(content_type, {})
        schema = content_data.get("schema", {})

        return Response(
            status_code=status_code,
            description=data.get("description", ""),
            content_type=content_type,
            schema_ref=schema.get("$ref"),
            schema=schema if "$ref" not in schema else None,
        )

    def resolve_ref(self, ref: str) -> Dict[str, Any]:
        """
        Resolve $ref pointer.

        Example: #/components/schemas/Memory -> returns Memory schema
        """
        if not ref.startswith("#/"):
            raise ValueError(f"Only local refs supported: {ref}")

        parts = ref[2:].split("/")
        result = self.raw_spec

        for part in parts:
            result = result[part]

        return result

    def get_schema_name_from_ref(self, ref: str) -> str:
        """Extract schema name from $ref"""
        return ref.split("/")[-1]
