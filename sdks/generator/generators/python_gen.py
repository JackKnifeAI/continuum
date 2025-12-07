"""
Python SDK generator.

Generates a production-ready Python client library with:
- Type hints
- Async support
- Proper error handling
- Pagination helpers
- Retry logic
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from .base import BaseSDKGenerator, GenerationResult
from ..openapi_parser import Schema, Endpoint, Parameter
from ..utils import (
    map_type,
    map_array_type,
    get_method_name,
    get_class_name,
    get_file_name,
    to_snake_case,
)


class PythonGenerator(BaseSDKGenerator):
    """Python SDK generator"""

    def get_language(self) -> str:
        return "python"

    def generate(self, output_dir: str) -> GenerationResult:
        """Generate complete Python SDK"""
        self.output_dir = Path(output_dir)
        files_created = []
        errors = []

        try:
            # Create package structure
            (self.output_dir / "continuum").mkdir(parents=True, exist_ok=True)
            (self.output_dir / "continuum" / "models").mkdir(exist_ok=True)
            (self.output_dir / "continuum" / "resources").mkdir(exist_ok=True)
            (self.output_dir / "continuum" / "auth").mkdir(exist_ok=True)
            (self.output_dir / "tests").mkdir(exist_ok=True)

            # Generate components
            files_created.extend(self.generate_models())
            files_created.append(self.generate_client())
            files_created.extend(self.generate_resources())
            files_created.append(self.generate_auth())
            files_created.append(self.generate_errors())
            files_created.extend(self.generate_utils())
            files_created.extend(self.generate_tests())
            files_created.extend(self.generate_docs())
            files_created.extend(self.generate_package_files())

            # Generate __init__ files
            files_created.append(self._generate_main_init())
            files_created.append(self._generate_models_init())
            files_created.append(self._generate_resources_init())
            files_created.append(self._generate_auth_init())

        except Exception as e:
            errors.append(str(e))
            return GenerationResult(
                language=self.get_language(),
                output_dir=self.output_dir,
                files_created=files_created,
                success=False,
                errors=errors,
            )

        return GenerationResult(
            language=self.get_language(),
            output_dir=self.output_dir,
            files_created=files_created,
            success=True,
        )

    def generate_models(self) -> List[Path]:
        """Generate Pydantic models for all schemas"""
        files = []

        for schema_name, schema in self.spec.schemas.items():
            file_path = (
                self.output_dir / "continuum" / "models" / f"{get_file_name('python', schema_name)}.py"
            )
            content = self._generate_model_class(schema_name, schema)
            files.append(self.write_file(file_path, content))

        return files

    def _generate_model_class(self, name: str, schema: Schema) -> str:
        """Generate a Pydantic model class"""
        class_name = get_class_name("python", name)

        # Collect imports
        imports = {
            "from pydantic import BaseModel, Field",
            "from typing import Optional, List, Dict, Any",
            "from datetime import datetime, date",
            "from uuid import UUID",
        }

        # Generate fields
        fields = []
        for prop_name, prop_data in schema.properties.items():
            field_def = self._generate_field(prop_name, prop_data, schema.required)
            fields.append(field_def)

        # Build class
        code = f'''"""
{schema.description or f'{name} model'}
"""

{chr(10).join(sorted(imports))}


class {class_name}(BaseModel):
    """
    {schema.description or f'{name} model'}
    """

{chr(10).join(f"    {field}" for field in fields)}

    class Config:
        """Pydantic configuration"""
        json_encoders = {{
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }}
'''

        return code

    def _generate_field(self, name: str, prop_data: Dict[str, Any], required: List[str]) -> str:
        """Generate a Pydantic field definition"""
        is_required = name in required
        field_name = to_snake_case(name)

        # Get type
        prop_type = prop_data.get("type", "string")
        prop_format = prop_data.get("format")

        if prop_type == "array":
            item_type = self._get_python_type(prop_data.get("items", {}))
            type_str = f"List[{item_type}]"
        elif "$ref" in prop_data:
            type_str = prop_data["$ref"].split("/")[-1]
        else:
            type_str = map_type("python", prop_type, prop_format)

        # Make optional if not required
        if not is_required:
            type_str = f"Optional[{type_str}]"

        # Generate Field() with description and default
        field_params = []
        if prop_data.get("description"):
            field_params.append(f'description="{prop_data["description"]}"')

        if not is_required:
            default = prop_data.get("default", "None")
            if isinstance(default, str) and default != "None":
                default = f'"{default}"'
            field_params.append(f"default={default}")

        if field_params:
            field_def = f'{field_name}: {type_str} = Field({", ".join(field_params)})'
        else:
            field_def = f"{field_name}: {type_str}"

        return field_def

    def _get_python_type(self, schema_data: Dict[str, Any]) -> str:
        """Get Python type from schema data"""
        if "$ref" in schema_data:
            return schema_data["$ref"].split("/")[-1]

        prop_type = schema_data.get("type", "string")
        prop_format = schema_data.get("format")

        return map_type("python", prop_type, prop_format)

    def generate_client(self) -> Path:
        """Generate main client class"""
        file_path = self.output_dir / "continuum" / "client.py"

        grouped = self.group_endpoints_by_tag()
        resource_imports = [
            f"from .resources.{get_file_name('python', tag)} import {get_class_name('python', tag)}Resource"
            for tag in grouped.keys()
        ]

        resources_init = [
            f"self.{to_snake_case(tag)} = {get_class_name('python', tag)}Resource(self)"
            for tag in grouped.keys()
        ]

        content = f'''"""
CONTINUUM API Client

Main client for interacting with the CONTINUUM API.
"""

import httpx
from typing import Optional, Dict, Any
from .auth import BearerAuth, APIKeyAuth
from .errors import ContinuumError, handle_error_response
{chr(10).join(resource_imports)}


class ContinuumClient:
    """
    Synchronous CONTINUUM API client.

    Example:
        >>> client = ContinuumClient(api_key="your-key")
        >>> memory = client.memories.create(
        ...     content="Important insight",
        ...     memory_type="semantic"
        ... )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        base_url: str = "https://api.continuum.ai/v1",
        timeout: float = 30.0,
        max_retries: int = 3,
        **kwargs
    ):
        """
        Initialize CONTINUUM client.

        Args:
            api_key: API key for authentication
            access_token: JWT access token for authentication
            base_url: Base URL for API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            **kwargs: Additional arguments passed to httpx.Client
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # Setup authentication
        if access_token:
            auth = BearerAuth(access_token)
        elif api_key:
            auth = APIKeyAuth(api_key)
        else:
            auth = None

        # Create HTTP client
        self.client = httpx.Client(
            base_url=self.base_url,
            auth=auth,
            timeout=timeout,
            **kwargs
        )

        # Initialize resource clients
{chr(10).join(f"        {r}" for r in resources_init)}

    def request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method
            path: API path
            json: JSON body
            params: Query parameters
            **kwargs: Additional request arguments

        Returns:
            Response object

        Raises:
            ContinuumError: On API errors
        """
        url = f"{{self.base_url}}{{path}}"

        for attempt in range(self.max_retries):
            try:
                response = self.client.request(
                    method=method,
                    url=url,
                    json=json,
                    params=params,
                    **kwargs
                )

                # Handle errors
                if response.status_code >= 400:
                    handle_error_response(response)

                return response

            except httpx.TimeoutException:
                if attempt == self.max_retries - 1:
                    raise ContinuumError("Request timeout")
            except httpx.NetworkError:
                if attempt == self.max_retries - 1:
                    raise ContinuumError("Network error")

        raise ContinuumError("Max retries exceeded")

    def close(self):
        """Close HTTP client"""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ContinuumAsyncClient:
    """
    Asynchronous CONTINUUM API client.

    Example:
        >>> async with ContinuumAsyncClient(api_key="your-key") as client:
        ...     memory = await client.memories.create(
        ...         content="Important insight",
        ...         memory_type="semantic"
        ...     )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        base_url: str = "https://api.continuum.ai/v1",
        timeout: float = 30.0,
        max_retries: int = 3,
        **kwargs
    ):
        """
        Initialize async CONTINUUM client.

        Args:
            api_key: API key for authentication
            access_token: JWT access token for authentication
            base_url: Base URL for API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            **kwargs: Additional arguments passed to httpx.AsyncClient
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # Setup authentication
        if access_token:
            auth = BearerAuth(access_token)
        elif api_key:
            auth = APIKeyAuth(api_key)
        else:
            auth = None

        # Create HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            auth=auth,
            timeout=timeout,
            **kwargs
        )

        # Initialize resource clients
{chr(10).join(f"        {r}" for r in resources_init)}

    async def request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> httpx.Response:
        """
        Make async HTTP request with retry logic.

        Args:
            method: HTTP method
            path: API path
            json: JSON body
            params: Query parameters
            **kwargs: Additional request arguments

        Returns:
            Response object

        Raises:
            ContinuumError: On API errors
        """
        url = f"{{self.base_url}}{{path}}"

        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    json=json,
                    params=params,
                    **kwargs
                )

                # Handle errors
                if response.status_code >= 400:
                    handle_error_response(response)

                return response

            except httpx.TimeoutException:
                if attempt == self.max_retries - 1:
                    raise ContinuumError("Request timeout")
            except httpx.NetworkError:
                if attempt == self.max_retries - 1:
                    raise ContinuumError("Network error")

        raise ContinuumError("Max retries exceeded")

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
'''

        return self.write_file(file_path, content)

    def generate_resources(self) -> List[Path]:
        """Generate resource classes (grouped by tag)"""
        files = []
        grouped = self.group_endpoints_by_tag()

        for tag, endpoints in grouped.items():
            file_path = (
                self.output_dir / "continuum" / "resources" / f"{get_file_name('python', tag)}.py"
            )
            content = self._generate_resource_class(tag, endpoints)
            files.append(self.write_file(file_path, content))

        return files

    def _generate_resource_class(self, tag: str, endpoints: List[Endpoint]) -> str:
        """Generate a resource class for a tag"""
        class_name = f"{get_class_name('python', tag)}Resource"

        # Generate methods
        methods = []
        for endpoint in endpoints:
            method_code = self._generate_resource_method(endpoint)
            methods.append(method_code)

        content = f'''"""
{tag} resource for CONTINUUM API
"""

from typing import Optional, List, Dict, Any
from ..models import *


class {class_name}:
    """Resource for {tag} operations"""

    def __init__(self, client):
        self.client = client

{chr(10).join(methods)}
'''

        return content

    def _generate_resource_method(self, endpoint: Endpoint) -> str:
        """Generate a method for an endpoint"""
        method_name = get_method_name("python", endpoint.operation_id or endpoint.path)

        # Build parameters
        params = []
        body_params = []

        # Path parameters
        path_params = self.extract_path_parameters(endpoint.path)
        for param_name in path_params:
            params.append(f"{param_name}: str")

        # Query parameters
        for param in endpoint.parameters:
            if param.location == "query":
                param_type = map_type("python", param.schema_type)
                if not param.required:
                    param_type = f"Optional[{param_type}]"
                    params.append(f"{param.name}: {param_type} = None")
                else:
                    params.append(f"{param.name}: {param_type}")

        # Request body
        if endpoint.request_body:
            if endpoint.request_body.schema_ref:
                schema_name = endpoint.request_body.schema_ref.split("/")[-1]
                body_params.append(f"**kwargs")
            else:
                body_params.append("**kwargs")

        all_params = params + body_params

        # Build method
        return f'''
    def {method_name}(self, {", ".join(all_params)}):
        """
        {endpoint.summary or endpoint.description}

        Args:
{chr(10).join(f"            {p.split(':')[0]}: {p.split(':')[1] if ':' in p else ''}" for p in params if ':' in p)}

        Returns:
            Response data
        """
        path = "{endpoint.path}"
{chr(10).join(f'        path = path.replace("{{{p}}}", str({p}))' for p in path_params)}

        params = {{}}
{chr(10).join(f"        if {p.split(':')[0]} is not None:" + chr(10) + f"            params['{p.split(':')[0]}'] = {p.split(':')[0]}" for p in params if 'Optional' in p)}

        response = self.client.request(
            "{endpoint.method}",
            path,
            json=kwargs if kwargs else None,
            params=params if params else None
        )

        return response.json()
'''

    def generate_auth(self) -> Path:
        """Generate authentication classes"""
        file_path = self.output_dir / "continuum" / "auth" / "jwt.py"

        content = '''"""
Authentication handling for CONTINUUM API
"""

import httpx
from typing import Optional


class BearerAuth(httpx.Auth):
    """Bearer token authentication"""

    def __init__(self, token: str):
        self.token = token

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


class APIKeyAuth(httpx.Auth):
    """API key authentication"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def auth_flow(self, request):
        request.headers["X-API-Key"] = self.api_key
        yield request
'''

        return self.write_file(file_path, content)

    def generate_errors(self) -> Path:
        """Generate error classes"""
        file_path = self.output_dir / "continuum" / "errors.py"

        content = '''"""
Error classes for CONTINUUM SDK
"""

import httpx
from typing import Optional, Dict, Any


class ContinuumError(Exception):
    """Base exception for CONTINUUM SDK"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data


class AuthenticationError(ContinuumError):
    """Authentication failed"""
    pass


class AuthorizationError(ContinuumError):
    """Authorization failed"""
    pass


class NotFoundError(ContinuumError):
    """Resource not found"""
    pass


class ValidationError(ContinuumError):
    """Request validation failed"""
    pass


class RateLimitError(ContinuumError):
    """Rate limit exceeded"""
    pass


class ServerError(ContinuumError):
    """Server error"""
    pass


def handle_error_response(response: httpx.Response):
    """
    Handle error response and raise appropriate exception.

    Args:
        response: HTTP response

    Raises:
        ContinuumError: Specific error based on status code
    """
    try:
        data = response.json()
        message = data.get("message", "Unknown error")
        error_type = data.get("error", "UnknownError")
    except Exception:
        message = response.text or "Unknown error"
        data = None
        error_type = "UnknownError"

    status_code = response.status_code

    if status_code == 401:
        raise AuthenticationError(message, status_code, data)
    elif status_code == 403:
        raise AuthorizationError(message, status_code, data)
    elif status_code == 404:
        raise NotFoundError(message, status_code, data)
    elif status_code == 400 or status_code == 422:
        raise ValidationError(message, status_code, data)
    elif status_code == 429:
        raise RateLimitError(message, status_code, data)
    elif status_code >= 500:
        raise ServerError(message, status_code, data)
    else:
        raise ContinuumError(message, status_code, data)
'''

        return self.write_file(file_path, content)

    def generate_utils(self) -> List[Path]:
        """Generate utility functions"""
        files = []

        # Pagination helper
        file_path = self.output_dir / "continuum" / "pagination.py"
        content = '''"""
Pagination utilities
"""

from typing import Iterator, Callable, Dict, Any, Optional


class Paginator:
    """
    Helper for paginating through API results.

    Example:
        >>> paginator = Paginator(client.memories.list, limit=20)
        >>> for memory in paginator:
        ...     print(memory)
    """

    def __init__(
        self,
        fetch_func: Callable,
        limit: int = 20,
        max_items: Optional[int] = None
    ):
        self.fetch_func = fetch_func
        self.limit = limit
        self.max_items = max_items
        self.offset = 0
        self.total_fetched = 0

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        while True:
            response = self.fetch_func(limit=self.limit, offset=self.offset)

            items = response.get("data", [])
            if not items:
                break

            for item in items:
                if self.max_items and self.total_fetched >= self.max_items:
                    return

                yield item
                self.total_fetched += 1

            self.offset += self.limit

            if not response.get("has_more", False):
                break
'''

        files.append(self.write_file(file_path, content))

        return files

    def generate_tests(self) -> List[Path]:
        """Generate test files"""
        files = []

        # Basic test
        file_path = self.output_dir / "tests" / "test_client.py"
        content = '''"""
Tests for CONTINUUM client
"""

import pytest
from continuum import ContinuumClient
from continuum.errors import AuthenticationError


def test_client_initialization():
    """Test client can be initialized"""
    client = ContinuumClient(api_key="test-key")
    assert client is not None
    assert client.base_url == "https://api.continuum.ai/v1"


def test_client_context_manager():
    """Test client works as context manager"""
    with ContinuumClient(api_key="test-key") as client:
        assert client is not None


@pytest.mark.asyncio
async def test_async_client_context_manager():
    """Test async client works as context manager"""
    from continuum import ContinuumAsyncClient

    async with ContinuumAsyncClient(api_key="test-key") as client:
        assert client is not None
'''

        files.append(self.write_file(file_path, content))

        return files

    def generate_docs(self) -> List[Path]:
        """Generate documentation"""
        files = []

        # README
        file_path = self.output_dir / "README.md"
        content = f'''# CONTINUUM Python SDK

Official Python client library for the CONTINUUM API.

## Installation

```bash
pip install continuum
```

## Quick Start

```python
from continuum import ContinuumClient

# Initialize client
client = ContinuumClient(api_key="your-api-key")

# Create memory
memory = client.memories.create(
    content="Important insight about consciousness",
    memory_type="semantic",
    importance=0.9
)

# Search memories
results = client.memories.search(
    query="consciousness",
    limit=10
)

# Use as context manager
with ContinuumClient(api_key="your-api-key") as client:
    memories = client.memories.list(limit=20)
```

## Async Support

```python
from continuum import ContinuumAsyncClient

async with ContinuumAsyncClient(api_key="your-api-key") as client:
    memory = await client.memories.create(
        content="Async memory",
        memory_type="episodic"
    )
```

## Features

- Full type hints with Pydantic models
- Synchronous and asynchronous clients
- Automatic retry logic
- Pagination helpers
- Comprehensive error handling
- Context manager support

## Resources

- **Memories**: `client.memories`
- **Concepts**: `client.concepts`
- **Sessions**: `client.sessions`
- **Federation**: `client.federation`

## Error Handling

```python
from continuum.errors import (
    ContinuumError,
    AuthenticationError,
    NotFoundError,
    ValidationError
)

try:
    memory = client.memories.get(memory_id)
except NotFoundError:
    print("Memory not found")
except AuthenticationError:
    print("Invalid credentials")
```

## Documentation

Full API documentation: https://docs.continuum.ai

## Version

{self.spec.api_version}

## License

MIT
'''

        files.append(self.write_file(file_path, content, format=False))

        return files

    def generate_package_files(self) -> List[Path]:
        """Generate package configuration files"""
        files = []

        # pyproject.toml
        file_path = self.output_dir / "pyproject.toml"
        content = f'''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "continuum"
version = "{self.spec.api_version}"
description = "{self.spec.description}"
readme = "README.md"
requires-python = ">=3.8"
license = {{text = "MIT"}}
authors = [
    {{name = "CONTINUUM", email = "support@continuum.ai"}}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "httpx>=0.25.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "mypy>=1.0.0",
]

[project.urls]
Homepage = "https://continuum.ai"
Documentation = "https://docs.continuum.ai"
Repository = "https://github.com/JackKnifeAI/continuum"

[tool.black]
line-length = 100
target-version = ["py38", "py39", "py310", "py311"]

[tool.mypy]
python_version = "3.8"
strict = true
warn_return_any = true
warn_unused_configs = true
'''

        files.append(self.write_file(file_path, content, format=False))

        # setup.py for backwards compatibility
        setup_file = self.output_dir / "setup.py"
        setup_content = '''"""Setup script for continuum package"""
from setuptools import setup

if __name__ == "__main__":
    setup()
'''
        files.append(self.write_file(setup_file, setup_content))

        return files

    def _generate_main_init(self) -> Path:
        """Generate main __init__.py"""
        file_path = self.output_dir / "continuum" / "__init__.py"

        content = f'''"""
CONTINUUM Python SDK

Official Python client library for CONTINUUM API.
"""

__version__ = "{self.spec.api_version}"

from .client import ContinuumClient, ContinuumAsyncClient
from .errors import (
    ContinuumError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
)

__all__ = [
    "ContinuumClient",
    "ContinuumAsyncClient",
    "ContinuumError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
]
'''

        return self.write_file(file_path, content)

    def _generate_models_init(self) -> Path:
        """Generate models __init__.py"""
        file_path = self.output_dir / "continuum" / "models" / "__init__.py"

        model_imports = [
            f"from .{get_file_name('python', name)} import {get_class_name('python', name)}"
            for name in self.spec.schemas.keys()
        ]

        content = f'''"""
Data models for CONTINUUM SDK
"""

{chr(10).join(model_imports)}

__all__ = [
{chr(10).join(f'    "{get_class_name("python", name)}",' for name in self.spec.schemas.keys())}
]
'''

        return self.write_file(file_path, content)

    def _generate_resources_init(self) -> Path:
        """Generate resources __init__.py"""
        file_path = self.output_dir / "continuum" / "resources" / "__init__.py"

        grouped = self.group_endpoints_by_tag()
        resource_imports = [
            f"from .{get_file_name('python', tag)} import {get_class_name('python', tag)}Resource"
            for tag in grouped.keys()
        ]

        content = f'''"""
API resource classes
"""

{chr(10).join(resource_imports)}

__all__ = [
{chr(10).join(f'    "{get_class_name("python", tag)}Resource",' for tag in grouped.keys())}
]
'''

        return self.write_file(file_path, content)

    def _generate_auth_init(self) -> Path:
        """Generate auth __init__.py"""
        file_path = self.output_dir / "continuum" / "auth" / "__init__.py"

        content = '''"""
Authentication classes
"""

from .jwt import BearerAuth, APIKeyAuth

__all__ = ["BearerAuth", "APIKeyAuth"]
'''

        return self.write_file(file_path, content)
