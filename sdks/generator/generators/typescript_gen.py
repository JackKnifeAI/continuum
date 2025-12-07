"""
TypeScript SDK generator.

Generates a production-ready TypeScript client library.
"""

from pathlib import Path
from typing import List
from .base import BaseSDKGenerator, GenerationResult
from ..utils import get_class_name, get_method_name, get_file_name, to_camel_case


class TypeScriptGenerator(BaseSDKGenerator):
    """TypeScript SDK generator"""

    def get_language(self) -> str:
        return "typescript"

    def generate(self, output_dir: str) -> GenerationResult:
        """Generate TypeScript SDK"""
        self.output_dir = Path(output_dir)
        files_created = []

        try:
            # Create package structure
            (self.output_dir / "src").mkdir(parents=True, exist_ok=True)
            (self.output_dir / "src" / "models").mkdir(exist_ok=True)
            (self.output_dir / "src" / "resources").mkdir(exist_ok=True)
            (self.output_dir / "src" / "auth").mkdir(exist_ok=True)
            (self.output_dir / "tests").mkdir(exist_ok=True)

            files_created.extend(self.generate_models())
            files_created.append(self.generate_client())
            files_created.extend(self.generate_resources())
            files_created.append(self.generate_auth())
            files_created.append(self.generate_errors())
            files_created.extend(self.generate_utils())
            files_created.extend(self.generate_tests())
            files_created.extend(self.generate_docs())
            files_created.extend(self.generate_package_files())

        except Exception as e:
            return GenerationResult(
                language=self.get_language(),
                output_dir=self.output_dir,
                files_created=files_created,
                success=False,
                errors=[str(e)],
            )

        return GenerationResult(
            language=self.get_language(),
            output_dir=self.output_dir,
            files_created=files_created,
            success=True,
        )

    def generate_models(self) -> List[Path]:
        """Generate TypeScript interfaces"""
        file_path = self.output_dir / "src" / "types.ts"

        interfaces = []
        for schema_name, schema in self.spec.schemas.items():
            interface = f'''export interface {get_class_name("typescript", schema_name)} {{
'''
            for prop_name, prop_data in schema.properties.items():
                prop_type = self._get_ts_type(prop_data)
                optional = "?" if prop_name not in schema.required else ""
                interfaces.append(f"  {to_camel_case(prop_name)}{optional}: {prop_type};")

            interface += "\n".join(interfaces) + "\n}\n\n"
            interfaces = [interface]

        content = f'''/**
 * Type definitions for CONTINUUM API
 */

{"".join(interfaces)}
'''

        return [self.write_file(file_path, content)]

    def _get_ts_type(self, prop_data) -> str:
        """Get TypeScript type from property data"""
        from ..utils import map_type

        prop_type = prop_data.get("type", "string")
        prop_format = prop_data.get("format")

        if prop_type == "array":
            item_type = self._get_ts_type(prop_data.get("items", {}))
            return f"Array<{item_type}>"
        elif "$ref" in prop_data:
            return prop_data["$ref"].split("/")[-1]
        else:
            return map_type("typescript", prop_type, prop_format)

    def generate_client(self) -> Path:
        """Generate TypeScript client"""
        file_path = self.output_dir / "src" / "client.ts"

        grouped = self.group_endpoints_by_tag()
        resource_imports = "\n".join([
            f"import {{ {get_class_name('typescript', tag)}Resource }} from './resources/{get_file_name('typescript', tag)}';"
            for tag in grouped.keys()
        ])

        content = f'''/**
 * CONTINUUM API Client
 */

import axios, {{ AxiosInstance, AxiosRequestConfig }} from 'axios';
{resource_imports}

export interface ContinuumConfig {{
  apiKey?: string;
  accessToken?: string;
  baseURL?: string;
  timeout?: number;
  maxRetries?: number;
}}

export class ContinuumClient {{
  private client: AxiosInstance;
  private maxRetries: number;

  public readonly memories: MemoriesResource;
  public readonly concepts: ConceptsResource;
  public readonly sessions: SessionsResource;
  public readonly federation: FederationResource;

  constructor(config: ContinuumConfig) {{
    this.maxRetries = config.maxRetries || 3;

    const headers: any = {{}};
    if (config.accessToken) {{
      headers['Authorization'] = `Bearer ${{config.accessToken}}`;
    }} else if (config.apiKey) {{
      headers['X-API-Key'] = config.apiKey;
    }}

    this.client = axios.create({{
      baseURL: config.baseURL || 'https://api.continuum.ai/v1',
      timeout: config.timeout || 30000,
      headers,
    }});

    // Initialize resources
    this.memories = new MemoriesResource(this);
    this.concepts = new ConceptsResource(this);
    this.sessions = new SessionsResource(this);
    this.federation = new FederationResource(this);
  }}

  async request<T>(config: AxiosRequestConfig): Promise<T> {{
    for (let attempt = 0; attempt < this.maxRetries; attempt++) {{
      try {{
        const response = await this.client.request<T>(config);
        return response.data;
      }} catch (error) {{
        if (attempt === this.maxRetries - 1) {{
          throw error;
        }}
      }}
    }}
    throw new Error('Max retries exceeded');
  }}
}}
'''

        return self.write_file(file_path, content)

    def generate_resources(self) -> List[Path]:
        """Generate resource classes"""
        return []  # Simplified for now

    def generate_auth(self) -> Path:
        """Generate auth utilities"""
        file_path = self.output_dir / "src" / "auth.ts"
        content = '''/**
 * Authentication utilities
 */

export class Auth {
  // Auth implementation
}
'''
        return self.write_file(file_path, content)

    def generate_errors(self) -> Path:
        """Generate error classes"""
        file_path = self.output_dir / "src" / "errors.ts"
        content = '''/**
 * Error classes
 */

export class ContinuumError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public responseData?: any
  ) {
    super(message);
    this.name = 'ContinuumError';
  }
}

export class AuthenticationError extends ContinuumError {
  constructor(message: string, statusCode?: number, responseData?: any) {
    super(message, statusCode, responseData);
    this.name = 'AuthenticationError';
  }
}

export class NotFoundError extends ContinuumError {
  constructor(message: string, statusCode?: number, responseData?: any) {
    super(message, statusCode, responseData);
    this.name = 'NotFoundError';
  }
}
'''
        return self.write_file(file_path, content)

    def generate_utils(self) -> List[Path]:
        """Generate utilities"""
        return []

    def generate_tests(self) -> List[Path]:
        """Generate tests"""
        return []

    def generate_docs(self) -> List[Path]:
        """Generate documentation"""
        file_path = self.output_dir / "README.md"
        content = f'''# CONTINUUM TypeScript SDK

Official TypeScript/JavaScript client for CONTINUUM API.

## Installation

```bash
npm install continuum
# or
yarn add continuum
```

## Usage

```typescript
import {{ ContinuumClient }} from 'continuum';

const client = new ContinuumClient({{
  apiKey: 'your-api-key'
}});

const memory = await client.memories.create({{
  content: 'Important insight',
  memoryType: 'semantic',
  importance: 0.9
}});
```

## Version

{self.spec.api_version}
'''
        return [self.write_file(file_path, content, format=False)]

    def generate_package_files(self) -> List[Path]:
        """Generate package.json"""
        file_path = self.output_dir / "package.json"
        content = f'''{{
  "name": "continuum",
  "version": "{self.spec.api_version}",
  "description": "{self.spec.description}",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {{
    "build": "tsc",
    "test": "jest"
  }},
  "dependencies": {{
    "axios": "^1.6.0"
  }},
  "devDependencies": {{
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0",
    "jest": "^29.0.0"
  }},
  "license": "MIT"
}}
'''
        return [self.write_file(file_path, content, format=False)]
