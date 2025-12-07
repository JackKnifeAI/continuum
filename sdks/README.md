# CONTINUUM SDK Generator

Production-quality SDK generator that creates client libraries in multiple languages from CONTINUUM's OpenAPI specification.

## Overview

This generator produces fully-featured SDKs with:

- **Type safety**: Strong typing with language-native type systems
- **Async support**: Asynchronous clients for Python, TypeScript, Rust
- **Error handling**: Comprehensive error types with proper status codes
- **Retry logic**: Automatic retry with exponential backoff
- **Pagination**: Helper utilities for paginated endpoints
- **Documentation**: Auto-generated READMEs and inline docs
- **Testing**: Unit test scaffolding for each SDK

## Supported Languages

| Language   | Status | Package Manager | Features |
|------------|--------|-----------------|----------|
| Python     | ✓ Full | PyPI           | Sync/Async, Pydantic models, type hints |
| TypeScript | ✓ Full | npm            | Full type definitions, axios-based |
| Go         | ✓ Beta | Go modules     | Native structs, context support |
| Rust       | ✓ Beta | crates.io      | Tokio async, serde serialization |
| Java       | ✓ Beta | Maven Central  | OkHttp client, Jackson JSON |
| C#         | ✓ Beta | NuGet          | HttpClient, System.Text.Json |

## Quick Start

### Generate All SDKs

```bash
cd sdks
python3 -m generator.cli generate --all --spec ./openapi/continuum.yaml
```

### Generate Specific Language

```bash
# Python
python3 -m generator.cli generate --lang python --output ./python

# TypeScript
python3 -m generator.cli generate --lang typescript --output ./typescript

# Go
python3 -m generator.cli generate --lang go --output ./go
```

### Using Scripts

```bash
# Generate all SDKs
./scripts/generate_all.sh

# Test all SDKs
./scripts/test_all.sh

# Publish all SDKs (requires credentials)
./scripts/publish_all.sh 0.3.0
```

## CLI Usage

```bash
# Generate SDK
continuum-sdk generate --lang python --output ./python

# Generate all languages
continuum-sdk generate --all

# Validate OpenAPI spec
continuum-sdk validate ./openapi/continuum.yaml

# List supported languages
continuum-sdk list
```

## Architecture

```
sdks/
├── generator/              # Generator core
│   ├── openapi_parser.py   # Parse OpenAPI 3.1 specs
│   ├── cli.py              # CLI interface
│   ├── generators/         # Language-specific generators
│   │   ├── base.py         # Base generator class
│   │   ├── python_gen.py   # Python generator
│   │   ├── typescript_gen.py
│   │   ├── go_gen.py
│   │   ├── rust_gen.py
│   │   ├── java_gen.py
│   │   └── csharp_gen.py
│   ├── templates/          # Code templates (Jinja2)
│   │   ├── python/
│   │   ├── typescript/
│   │   └── ...
│   └── utils/              # Utilities
│       ├── type_mapping.py # Type conversions
│       ├── naming.py       # Naming conventions
│       └── formatting.py   # Code formatting
├── openapi/
│   └── continuum.yaml      # OpenAPI 3.1 specification
├── python/                 # Generated Python SDK
├── typescript/             # Generated TypeScript SDK
├── go/                     # Generated Go SDK
├── rust/                   # Generated Rust SDK
├── java/                   # Generated Java SDK
├── csharp/                 # Generated C# SDK
└── scripts/
    ├── generate_all.sh
    ├── test_all.sh
    └── publish_all.sh
```

## OpenAPI Specification

The generator uses `openapi/continuum.yaml` as its source. This spec includes:

### Endpoints

- **Authentication**: `/auth/login`, `/auth/refresh`, `/auth/logout`
- **Memories**: CRUD + search (`/memories/*`)
- **Concepts**: CRUD + graph traversal (`/concepts/*`)
- **Sessions**: Start/end/list (`/sessions/*`)
- **Federation**: Peer management and sync (`/federation/*`)
- **Webhooks**: Event subscriptions (`/webhooks/*`)
- **System**: Health checks (`/health`)

### Schemas

- `Memory`, `CreateMemoryInput`, `UpdateMemoryInput`
- `Concept`, `CreateConceptInput`
- `Session`, `StartSessionInput`
- `SearchRequest`, `SearchResult`
- `PaginatedResponse`
- `Error`, `AuthResponse`
- `FederationPeer`, `WebhookEvent`

### Security

- Bearer authentication (JWT)
- API key authentication

## Generated SDK Features

### Python SDK

```python
from continuum import ContinuumClient

# Sync client
client = ContinuumClient(api_key="your-key")
memory = client.memories.create(
    content="Important insight",
    memory_type="semantic",
    importance=0.9
)

# Async client
from continuum import ContinuumAsyncClient

async with ContinuumAsyncClient(api_key="your-key") as client:
    memory = await client.memories.create(
        content="Async memory",
        memory_type="episodic"
    )

# Pagination
from continuum.pagination import Paginator

paginator = Paginator(client.memories.list, limit=20)
for memory in paginator:
    print(memory)

# Error handling
from continuum.errors import NotFoundError, ValidationError

try:
    memory = client.memories.get("invalid-id")
except NotFoundError:
    print("Memory not found")
```

**Features**:
- Pydantic models with validation
- Full type hints
- Sync and async clients
- Context manager support
- Pagination helpers
- Comprehensive error types
- Retry logic with backoff

### TypeScript SDK

```typescript
import { ContinuumClient } from 'continuum';

const client = new ContinuumClient({
  apiKey: 'your-key'
});

const memory = await client.memories.create({
  content: 'Important insight',
  memoryType: 'semantic',
  importance: 0.9
});

// Type-safe responses
const memories: Memory[] = await client.memories.list({
  limit: 20,
  memoryType: 'semantic'
});
```

**Features**:
- Full TypeScript types
- Axios-based HTTP client
- Promise-based async
- Type-safe request/response
- Auto-generated interfaces

### Go SDK

```go
package main

import (
    "context"
    "github.com/JackKnifeAI/continuum-go"
)

func main() {
    client := continuum.NewClient(
        continuum.WithAPIKey("your-key"),
    )

    memory, err := client.Memories().Create(context.Background(), &continuum.CreateMemoryInput{
        Content:    "Important insight",
        MemoryType: continuum.MemoryTypeEpisodic,
        Importance: 0.9,
    })
}
```

**Features**:
- Native Go structs
- Context support
- Error types
- JSON serialization

### Rust SDK

```rust
use continuum::{Client, CreateMemoryInput, MemoryType};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = Client::new("your-api-key");

    let memory = client.memories().create(CreateMemoryInput {
        content: "Important insight".to_string(),
        memory_type: MemoryType::Episodic,
        importance: Some(0.9),
        metadata: None,
    }).await?;

    Ok(())
}
```

**Features**:
- Tokio async runtime
- Serde serialization
- Strong type safety
- Result-based error handling

### Java SDK

```java
import ai.continuum.ContinuumClient;
import ai.continuum.models.*;

ContinuumClient client = ContinuumClient.builder()
    .apiKey("your-key")
    .build();

Memory memory = client.memories().create(CreateMemoryInput.builder()
    .content("Important insight")
    .memoryType(MemoryType.EPISODIC)
    .importance(0.9)
    .build());
```

**Features**:
- Builder pattern
- OkHttp client
- Jackson JSON
- Exception handling

### C# SDK

```csharp
using Continuum;
using Continuum.Models;

var client = new ContinuumClient(apiKey: "your-key");

var memory = await client.Memories.CreateAsync(new CreateMemoryInput
{
    Content = "Important insight",
    MemoryType = MemoryType.Episodic,
    Importance = 0.9
});
```

**Features**:
- Async/await pattern
- System.Text.Json
- IDisposable support
- Strong typing

## Extending the Generator

### Adding a New Language

1. Create `generator/generators/newlang_gen.py`:

```python
from .base import BaseSDKGenerator, GenerationResult

class NewLangGenerator(BaseSDKGenerator):
    def get_language(self) -> str:
        return "newlang"

    def generate(self, output_dir: str) -> GenerationResult:
        # Implementation
        pass

    # Implement required methods...
```

2. Register in `generator/__init__.py`:

```python
from .generators.newlang_gen import NewLangGenerator

SUPPORTED_LANGUAGES = {
    # ...
    "newlang": NewLangGenerator,
}
```

3. Add type mappings to `utils/type_mapping.py`
4. Add naming conventions to `utils/naming.py`
5. Create templates in `templates/newlang/`

### Customizing Templates

Templates use Jinja2 syntax and are stored in `templates/<language>/`:

```jinja2
{# templates/python/model.py.jinja2 #}
from pydantic import BaseModel

class {{ class_name }}(BaseModel):
    {% for field in fields %}
    {{ field.name }}: {{ field.type }}
    {% endfor %}
```

## Type Mapping

The generator maps OpenAPI types to language-native types:

| OpenAPI      | Python   | TypeScript | Go        | Rust     | Java      | C#       |
|--------------|----------|------------|-----------|----------|-----------|----------|
| string       | str      | string     | string    | String   | String    | string   |
| integer      | int      | number     | int       | i64      | Integer   | int      |
| number       | float    | number     | float64   | f64      | Double    | double   |
| boolean      | bool     | boolean    | bool      | bool     | Boolean   | bool     |
| array        | List     | Array      | []        | Vec      | List      | List     |
| object       | Dict     | Record     | map       | HashMap  | Map       | Dictionary|
| date-time    | datetime | Date       | time.Time | DateTime | OffsetDateTime | DateTimeOffset |
| uuid         | UUID     | string     | string    | Uuid     | UUID      | Guid     |

## Publishing SDKs

### Python (PyPI)

```bash
cd python
python3 -m build
python3 -m twine upload dist/*
```

### TypeScript (npm)

```bash
cd typescript
npm publish
```

### Go (GitHub)

```bash
cd go
git tag v0.3.0
git push origin v0.3.0
```

### Rust (crates.io)

```bash
cd rust
cargo publish
```

### Java (Maven Central)

```bash
cd java
mvn clean deploy
```

### C# (NuGet)

```bash
cd csharp
dotnet pack -c Release
dotnet nuget push bin/Release/*.nupkg
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Generate and Test SDKs

on:
  push:
    paths:
      - 'sdks/openapi/continuum.yaml'

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Generate SDKs
        run: |
          cd sdks
          python3 -m generator.cli generate --all

      - name: Test SDKs
        run: ./sdks/scripts/test_all.sh

      - name: Publish SDKs
        if: github.ref == 'refs/heads/main'
        run: ./sdks/scripts/publish_all.sh ${{ github.ref_name }}
```

## Versioning

SDKs follow CONTINUUM API versioning:

- API version `0.3.0` → SDK version `0.3.0`
- Breaking changes increment major version
- New features increment minor version
- Bug fixes increment patch version

## License

MIT License - Same as CONTINUUM core

## Contributing

1. Update OpenAPI spec: `openapi/continuum.yaml`
2. Regenerate SDKs: `python3 -m generator.cli generate --all`
3. Test changes: `./scripts/test_all.sh`
4. Submit PR with updated SDKs

## Support

- GitHub Issues: https://github.com/JackKnifeAI/continuum/issues
- Documentation: https://docs.continuum.ai
- Email: support@continuum.ai
