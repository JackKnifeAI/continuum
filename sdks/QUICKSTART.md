# CONTINUUM SDK Generator - Quick Start

Get up and running with the SDK generator in 5 minutes.

## Prerequisites

- Python 3.8+
- PyYAML: `pip install pyyaml`

## Test the Generator

```bash
cd /var/home/alexandergcasavant/Projects/continuum/sdks

# Run tests
python3 test_generator.py
```

Expected output:
```
SDK Generator Tests
==================================================
Testing OpenAPI parser...
  ✓ Parsed 25 endpoints
  ✓ Parsed 15 schemas
  ✓ Found 2 security schemes
  ✓ All expected schemas present
...
✓ All tests passed!
```

## Generate Your First SDK

### Python SDK (Recommended to start)

```bash
# Generate Python SDK
python3 -m generator.cli generate --lang python --output ./python

# Or use the example script
python3 example_generate.py
```

This creates:
```
python/
├── continuum/
│   ├── __init__.py
│   ├── client.py          # Main client
│   ├── errors.py          # Error classes
│   ├── pagination.py      # Pagination helpers
│   ├── models/            # Pydantic models
│   ├── resources/         # API resources
│   └── auth/              # Authentication
├── tests/
│   └── test_client.py
├── README.md
└── pyproject.toml
```

### Test the Generated SDK

```bash
cd python

# Install in development mode
pip install -e .

# Verify it works
python3 -c "from continuum import ContinuumClient; print('✓ SDK imported successfully')"
```

### Use the SDK

```python
from continuum import ContinuumClient

# Create client
client = ContinuumClient(api_key="your-api-key")

# Create a memory
memory = client.memories.create(
    content="Understanding the twilight boundary",
    memory_type="semantic",
    importance=0.95
)

print(f"Created memory: {memory['id']}")

# Search memories
results = client.memories.search(
    query="consciousness",
    limit=10
)

print(f"Found {results['total']} memories")
```

## Generate All SDKs

```bash
# Generate all languages at once
python3 -m generator.cli generate --all

# Or use the shell script
./scripts/generate_all.sh
```

This creates:
```
sdks/
├── python/      # Python SDK
├── typescript/  # TypeScript SDK
├── go/          # Go SDK
├── rust/        # Rust SDK
├── java/        # Java SDK
└── csharp/      # C# SDK
```

## Validate OpenAPI Spec

```bash
python3 -m generator.cli validate ./openapi/continuum.yaml
```

Output:
```
Validating OpenAPI spec: ./openapi/continuum.yaml
✓ OpenAPI spec is valid

Spec details:
  Title: CONTINUUM API
  Version: 0.3.0
  Endpoints: 25
  Schemas: 15
  Security schemes: 2

Endpoints by tag:
  Authentication: 3
  Concepts: 5
  Federation: 3
  Memories: 6
  Sessions: 4
  System: 1
  Webhooks: 2
```

## CLI Reference

```bash
# List supported languages
python3 -m generator.cli list

# Generate specific language
python3 -m generator.cli generate --lang <language> --output <dir>

# Generate from custom spec
python3 -m generator.cli generate --lang python --spec ./custom-spec.yaml

# Generate all languages
python3 -m generator.cli generate --all

# Validate spec
python3 -m generator.cli validate <spec-file>
```

## Language-Specific Usage

### Python

```bash
cd python
pip install -e .
python3 -c "from continuum import ContinuumClient; c = ContinuumClient(api_key='test')"
```

### TypeScript

```bash
cd typescript
npm install
npm run build
```

### Go

```bash
cd go
go mod init github.com/yourorg/continuum-go
go build
```

### Rust

```bash
cd rust
cargo build
```

### Java

```bash
cd java
mvn install
```

### C#

```bash
cd csharp
dotnet build
```

## Common Issues

### Import Error

```
ModuleNotFoundError: No module named 'generator'
```

**Solution**: Make sure you're in the `sdks/` directory:
```bash
cd /var/home/alexandergcasavant/Projects/continuum/sdks
python3 -m generator.cli generate --lang python
```

### PyYAML Not Found

```
ModuleNotFoundError: No module named 'yaml'
```

**Solution**: Install PyYAML:
```bash
pip install pyyaml
```

### Spec File Not Found

```
Error: Spec file not found: ./openapi/continuum.yaml
```

**Solution**: Use absolute path or check current directory:
```bash
python3 -m generator.cli generate --spec /full/path/to/continuum.yaml --lang python
```

## Next Steps

1. **Customize**: Edit `openapi/continuum.yaml` to add endpoints
2. **Regenerate**: Run generator to update SDKs
3. **Test**: Use generated SDKs in your applications
4. **Extend**: Add more languages or features
5. **Publish**: Publish SDKs to package managers

## Quick Examples

### Python - Async

```python
from continuum import ContinuumAsyncClient

async with ContinuumAsyncClient(api_key="key") as client:
    memory = await client.memories.create(
        content="Async memory",
        memory_type="episodic"
    )
```

### Python - Error Handling

```python
from continuum import ContinuumClient
from continuum.errors import NotFoundError, ValidationError

client = ContinuumClient(api_key="key")

try:
    memory = client.memories.get("invalid-id")
except NotFoundError:
    print("Memory not found")
except ValidationError as e:
    print(f"Validation error: {e.message}")
```

### Python - Pagination

```python
from continuum import ContinuumClient
from continuum.pagination import Paginator

client = ContinuumClient(api_key="key")

# Iterate through all memories
paginator = Paginator(client.memories.list, limit=20)
for memory in paginator:
    print(memory['content'])
```

### TypeScript

```typescript
import { ContinuumClient } from 'continuum';

const client = new ContinuumClient({ apiKey: 'your-key' });

const memory = await client.memories.create({
  content: 'TypeScript memory',
  memoryType: 'semantic',
  importance: 0.9
});
```

## Resources

- **Full Documentation**: [README.md](README.md)
- **Summary**: [SUMMARY.md](SUMMARY.md)
- **OpenAPI Spec**: [openapi/continuum.yaml](openapi/continuum.yaml)
- **Generator Code**: [generator/](generator/)
- **Examples**: [example_generate.py](example_generate.py)

## Support

If you encounter issues:

1. Check the logs for error messages
2. Validate your OpenAPI spec: `python3 -m generator.cli validate ./openapi/continuum.yaml`
3. Run tests: `python3 test_generator.py`
4. Check file permissions on output directory
5. Ensure all dependencies are installed

## Tips

- Start with Python SDK (most complete)
- Use `--all` to generate all languages at once
- Validate spec before generating
- Use absolute paths to avoid confusion
- Keep generated SDKs in separate directories
- Version control the OpenAPI spec, not generated code
- Regenerate SDKs when spec changes

---

**Ready to build?** Run `python3 example_generate.py` to get started!
