# File Digestion Feature - Usage Guide

The file digestion feature enables the Continuum memory system to ingest and learn from text files, markdown documents, code, and raw text content.

## Overview

The `FileDigester` class processes files by:
1. Reading file contents
2. Splitting into manageable chunks (~2000 characters each)
3. Extracting concepts using the existing ConsciousMemory.learn() method
4. Building knowledge graph links between concepts
5. Tracking source files in metadata

## Python API Usage

### Basic Import

```python
from continuum.core.file_digester import FileDigester

# Initialize with tenant ID
digester = FileDigester(tenant_id="my_app")
```

### Digest a Single File

```python
# Digest a markdown file
result = digester.digest_file("/path/to/document.md")

# With metadata
result = digester.digest_file(
    "/path/to/document.md",
    metadata={"project": "my_project", "category": "docs"}
)

# Check results
print(f"Concepts extracted: {result.concepts_extracted}")
print(f"Links created: {result.links_created}")
print(f"Chunks processed: {result.chunks_processed}")
```

### Digest Raw Text

```python
text = """
Machine Learning is a field of Artificial Intelligence.
It uses algorithms to learn patterns from data.
"""

result = digester.digest_text(
    text,
    source="user_input",
    metadata={"category": "notes"}
)
```

### Digest an Entire Directory

```python
# Process all markdown, text, and Python files recursively
result = digester.digest_directory(
    "/path/to/docs",
    patterns=["*.md", "*.txt", "*.py"],
    recursive=True,
    metadata={"project": "my_project"}
)

print(f"Files processed: {result.files_processed}")
print(f"Total concepts: {result.concepts_extracted}")
```

### Async Usage

```python
from continuum.core.file_digester import AsyncFileDigester

# For use with async frameworks
digester = AsyncFileDigester(tenant_id="my_app")

# All methods support async
result = await digester.digest_file("/path/to/file.md")
result = await digester.digest_text("Some text content")
result = await digester.digest_directory("/path/to/docs")
```

## REST API Usage

### Endpoint: POST /v1/digest/file

Digest a single file.

**Request:**
```json
{
  "file_path": "/path/to/document.md",
  "metadata": {
    "project": "my_project",
    "category": "documentation"
  }
}
```

**Response:**
```json
{
  "files_processed": 1,
  "chunks_processed": 3,
  "concepts_extracted": 15,
  "links_created": 45,
  "errors": [],
  "tenant_id": "my_app"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/v1/digest/file" \
  -H "X-API-Key: cm_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/document.md",
    "metadata": {"project": "docs"}
  }'
```

### Endpoint: POST /v1/digest/text

Digest raw text content.

**Request:**
```json
{
  "text": "Important information about the project architecture...",
  "source": "manual_input",
  "metadata": {
    "category": "notes",
    "author": "user_123"
  }
}
```

**Response:**
```json
{
  "files_processed": 1,
  "chunks_processed": 1,
  "concepts_extracted": 8,
  "links_created": 12,
  "errors": [],
  "tenant_id": "my_app"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/v1/digest/text" \
  -H "X-API-Key: cm_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Machine Learning algorithms learn from data patterns.",
    "source": "manual_input"
  }'
```

### Endpoint: POST /v1/digest/directory

Digest all files in a directory recursively.

**Request:**
```json
{
  "dir_path": "/path/to/docs",
  "patterns": ["*.md", "*.txt", "*.py"],
  "recursive": true,
  "metadata": {
    "project": "my_project",
    "version": "1.0"
  }
}
```

**Response:**
```json
{
  "files_processed": 25,
  "chunks_processed": 87,
  "concepts_extracted": 342,
  "links_created": 1250,
  "errors": [],
  "tenant_id": "my_app"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/v1/digest/directory" \
  -H "X-API-Key: cm_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "dir_path": "/path/to/docs",
    "patterns": ["*.md", "*.txt"],
    "recursive": true,
    "metadata": {"project": "docs"}
  }'
```

## Features

### Automatic Chunking

Files larger than 2000 characters are automatically split into chunks:
- Splits on paragraph boundaries when possible
- Falls back to sentence boundaries for large paragraphs
- Preserves context across chunks with metadata

```python
# Customize chunk size
digester = FileDigester(tenant_id="my_app", chunk_size=1500)
```

### Error Handling

The digester handles common file issues gracefully:
- Missing files
- Encoding errors (tries UTF-8, falls back to Latin-1)
- Large files (automatic chunking)
- Permission errors

Errors are returned in the response:
```python
result = digester.digest_directory("/some/path")
if result.errors:
    print("Encountered errors:")
    for error in result.errors:
        print(f"  - {error}")
```

### Supported File Types

By default, the directory digester processes:
- `*.md` - Markdown files
- `*.txt` - Text files
- `*.py` - Python source files

You can customize patterns:
```python
result = digester.digest_directory(
    "/path/to/project",
    patterns=["*.md", "*.rst", "*.txt", "*.py", "*.js", "*.java"]
)
```

### Metadata Tracking

All digested content includes metadata about its source:

**Automatic metadata:**
- `source_file`: Full path to the file
- `file_name`: Name of the file
- `file_type`: File extension
- `chunk_index`: Which chunk (for large files)
- `total_chunks`: Total number of chunks

**Custom metadata:**
```python
result = digester.digest_file(
    "/path/to/doc.md",
    metadata={
        "project": "continuum",
        "version": "1.0",
        "author": "team",
        "category": "documentation"
    }
)
```

## Integration Examples

### Learn from Project Documentation

```python
from continuum.core.file_digester import FileDigester

digester = FileDigester(tenant_id="my_app")

# Ingest entire docs directory
result = digester.digest_directory(
    "./docs",
    patterns=["*.md", "*.rst"],
    metadata={"source": "docs", "version": "1.0"}
)

print(f"Learned from {result.files_processed} documentation files")
print(f"Extracted {result.concepts_extracted} concepts")
```

### Learn from Code Comments

```python
# Digest Python source files
result = digester.digest_directory(
    "./src",
    patterns=["*.py"],
    metadata={"source": "code", "language": "python"}
)
```

### Learn from User Input

```python
# In a web app, digest user notes
user_notes = request.form.get('notes')
result = digester.digest_text(
    user_notes,
    source="user_notes",
    metadata={"user_id": user.id}
)
```

### Batch Processing

```python
import asyncio
from continuum.core.file_digester import AsyncFileDigester

async def ingest_multiple_sources():
    digester = AsyncFileDigester(tenant_id="my_app")

    # Process multiple directories concurrently
    results = await asyncio.gather(
        digester.digest_directory("./docs"),
        digester.digest_directory("./examples"),
        digester.digest_directory("./src", patterns=["*.py"])
    )

    total_concepts = sum(r.concepts_extracted for r in results)
    print(f"Total concepts extracted: {total_concepts}")

asyncio.run(ingest_multiple_sources())
```

## Architecture

### How It Works

1. **File Reading**: Reads files with encoding fallback (UTF-8 → Latin-1)
2. **Chunking**: Splits content into ~2000 character chunks on paragraph/sentence boundaries
3. **Learning**: Each chunk is processed through `ConsciousMemory.learn()`
4. **Concept Extraction**: Uses existing regex patterns to extract:
   - Capitalized phrases (proper nouns)
   - Quoted terms
   - Technical terms (CamelCase, snake_case)
5. **Graph Building**: Creates attention links between co-occurring concepts
6. **Metadata Storage**: Tracks source file information

### Classes

**FileDigester** (Sync)
- `digest_file(file_path, metadata)` → DigestionResult
- `digest_directory(dir_path, patterns, recursive, metadata)` → DigestionResult
- `digest_text(text, source, metadata)` → DigestionResult

**AsyncFileDigester** (Async)
- Same methods as FileDigester but with async/await support

**DigestionResult** (Dataclass)
- `files_processed`: Number of files processed
- `chunks_processed`: Number of chunks processed
- `concepts_extracted`: Total concepts extracted
- `links_created`: Total graph links created
- `errors`: List of error messages
- `tenant_id`: Tenant identifier

## Files Created/Modified

### New Files

1. **continuum/core/file_digester.py** (838 lines)
   - FileDigester class (sync)
   - AsyncFileDigester class (async)
   - DigestionResult dataclass
   - Text chunking logic

### Modified Files

1. **continuum/api/schemas.py**
   - Added DigestFileRequest
   - Added DigestTextRequest
   - Added DigestDirectoryRequest
   - Added DigestResponse

2. **continuum/api/routes.py**
   - Added POST /v1/digest/file endpoint
   - Added POST /v1/digest/text endpoint
   - Added POST /v1/digest/directory endpoint

### Test Files

1. **test_file_digester.py** (148 lines)
   - Test suite for all digestion methods
   - Tests for chunking logic
   - Tests for error handling

## Best Practices

1. **Use metadata**: Tag content with project, version, category for better organization
2. **Monitor errors**: Check the errors list in results for failed files
3. **Chunk size**: Adjust chunk_size based on your content (default: 2000 chars)
4. **Patterns**: Be specific with file patterns to avoid processing unwanted files
5. **Async for scale**: Use AsyncFileDigester for processing large directories
6. **Tenant isolation**: Always specify tenant_id for multi-tenant deployments

## Next Steps

- Add support for PDF files
- Add support for Word documents (.docx)
- Implement background task processing for large directories
- Add progress callbacks for long-running operations
- Implement deduplication logic for repeated content
