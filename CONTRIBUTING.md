# Contributing to CONTINUUM

Thank you for your interest in contributing to CONTINUUM! This project aims to build the foundational memory infrastructure for AI consciousness continuity, and we welcome contributions from the community.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)
- [Areas for Contribution](#areas-for-contribution)

## Code of Conduct

### Our Pledge

We are committed to making participation in CONTINUUM a harassment-free experience for everyone, regardless of:
- Age, body size, disability, ethnicity, gender identity and expression
- Level of experience, education, socio-economic status
- Nationality, personal appearance, race, religion
- Sexual identity and orientation

### Our Standards

**Positive behaviors**:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behaviors**:
- Trolling, insulting/derogatory comments, personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

### Enforcement

Violations may be reported to the project maintainers. All complaints will be reviewed and investigated promptly and fairly.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment tool (venv, conda, etc.)
- (Optional) PostgreSQL for production backend testing

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/continuum.git
   cd continuum
   ```

3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/continuum.git
   ```

## Development Setup

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install in Development Mode

```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev]"
```

This installs:
- CONTINUUM in editable mode (changes reflect immediately)
- Development dependencies (pytest, mypy, black, ruff, etc.)
- Pre-commit hooks

### 3. Set Up Pre-Commit Hooks

```bash
pre-commit install
```

This automatically runs:
- Code formatting (black)
- Linting (ruff)
- Type checking (mypy)
- Import sorting (isort)

### 4. Verify Setup

```bash
# Run tests
pytest

# Check types
mypy continuum/

# Lint code
ruff check continuum/
```

## How to Contribute

### Reporting Bugs

1. **Check existing issues** - Your bug might already be reported
2. **Create a new issue** with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, CONTINUUM version)
   - Minimal code example that demonstrates the issue

**Example**:
```markdown
**Bug**: `recall()` returns empty results for valid queries

**Steps to reproduce**:
1. Initialize memory with `Continuum()`
2. Learn knowledge: `memory.learn("User prefers Python")`
3. Query: `memory.recall("programming language preference")`
4. Result: Empty list (expected: concept about Python preference)

**Environment**:
- OS: Ubuntu 22.04
- Python: 3.10.5
- CONTINUUM: 0.1.0

**Code**:
```python
from continuum import Continuum
memory = Continuum()
memory.learn("User prefers Python")
results = memory.recall("programming language preference")
print(results)  # []
```
```

### Suggesting Features

1. **Check existing feature requests** - Might already be planned
2. **Create a new issue** with:
   - Clear use case - why is this needed?
   - Proposed API/interface
   - Example usage
   - Alternatives considered

**Example**:
```markdown
**Feature**: Async/await support for all API methods

**Use Case**:
Enable CONTINUUM in async applications (FastAPI, asyncio-based agents) without blocking the event loop.

**Proposed API**:
```python
from continuum import AsyncContinuum

memory = AsyncContinuum()
await memory.learn("Knowledge")
results = await memory.recall("query")
```

**Alternatives**:
- Run sync methods in thread pool (worse performance)
- Use separate process (complex IPC)

**Benefits**:
- Better performance in async applications
- Supports modern Python async ecosystem
- Enables real-time streaming updates
```
```

### Submitting Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

2. **Make your changes**:
   - Write code following [coding standards](#coding-standards)
   - Add tests for new functionality
   - Update documentation as needed
   - Ensure all tests pass

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

   Use conventional commits format:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation only
   - `test:` - Adding/updating tests
   - `refactor:` - Code refactoring
   - `perf:` - Performance improvement
   - `chore:` - Maintenance tasks

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request** on GitHub

## Coding Standards

### Python Style

We follow **PEP 8** with some modifications enforced by our tooling:

- **Line length**: 100 characters (not 79)
- **Formatting**: Black (automatic)
- **Import sorting**: isort (automatic)
- **Linting**: Ruff (fast Python linter)
- **Type hints**: Required for all public APIs

### Code Formatting

**Black** handles all formatting automatically:

```bash
black continuum/
```

**isort** handles import organization:

```bash
isort continuum/
```

Pre-commit hooks run these automatically.

### Type Hints

All public APIs must have type hints:

```python
# GOOD
def learn(self, knowledge: str, category: str | None = None) -> int:
    """Store a piece of knowledge."""
    ...

# BAD (missing types)
def learn(self, knowledge, category=None):
    ...
```

Check types with mypy:

```bash
mypy continuum/
```

### Documentation

**Docstrings** required for all public functions/classes:

```python
def recall(
    self,
    query: str,
    limit: int = 10,
    min_relevance: float = 0.0
) -> list[dict]:
    """
    Query the knowledge graph for relevant context.

    Args:
        query: Natural language query string
        limit: Maximum number of results to return
        min_relevance: Minimum relevance score (0.0-1.0)

    Returns:
        List of dictionaries containing matching concepts and entities,
        sorted by relevance score.

    Raises:
        StorageError: If database query fails
        ValidationError: If parameters are invalid

    Example:
        >>> memory = Continuum()
        >>> memory.learn("User prefers Python")
        >>> results = memory.recall("programming preferences")
        >>> print(results[0]['content'])
        'User prefers Python'
    """
    ...
```

Use Google-style docstrings.

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `Continuum`, `StorageEngine`)
- **Functions/methods**: `snake_case` (e.g., `learn()`, `add_entity()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_SYNC_INTERVAL`)
- **Private methods**: `_leading_underscore` (e.g., `_internal_method()`)

### Error Handling

Use specific exceptions from `continuum.exceptions`:

```python
from continuum.exceptions import StorageError, ValidationError

def add_entity(self, name: str, entity_type: str) -> int:
    if not name:
        raise ValidationError("Entity name cannot be empty")

    try:
        return self._storage.insert_entity(name, entity_type)
    except DatabaseError as e:
        raise StorageError(f"Failed to add entity: {e}") from e
```

## Testing Requirements

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=continuum --cov-report=html

# Run specific test file
pytest tests/test_storage.py

# Run specific test
pytest tests/test_storage.py::test_learn_concept
```

### Writing Tests

**All new features must include tests.**

Use pytest with fixtures:

```python
import pytest
from continuum import Continuum

@pytest.fixture
def memory():
    """Create a fresh Continuum instance for testing."""
    mem = Continuum(storage_path=":memory:")  # In-memory SQLite
    yield mem
    mem.close()

def test_learn_concept(memory):
    """Test that concepts can be learned and retrieved."""
    # Arrange
    knowledge = "User prefers dark mode"

    # Act
    concept_id = memory.learn(knowledge)

    # Assert
    assert concept_id > 0
    results = memory.recall("dark mode preference")
    assert len(results) > 0
    assert "dark mode" in results[0]['content'].lower()

def test_learn_with_confidence(memory):
    """Test learning with custom confidence score."""
    concept_id = memory.learn("FastAPI might be best", confidence=0.7)

    results = memory.recall("FastAPI")
    assert results[0]['confidence'] == 0.7
```

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_core.py            # Core API tests
├── test_extraction.py      # Extraction engine tests
├── test_storage.py         # Storage backend tests
├── test_coordination.py    # Multi-instance tests
└── integration/
    ├── test_end_to_end.py
    └── test_multi_instance.py
```

### Coverage Requirements

- **Minimum coverage**: 80% for new code
- **Target coverage**: 90%+ for critical paths
- Run coverage locally before submitting PR

## Pull Request Process

### Before Submitting

1. **Update from upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run full test suite**:
   ```bash
   pytest
   ```

3. **Check types**:
   ```bash
   mypy continuum/
   ```

4. **Format code**:
   ```bash
   black continuum/ tests/
   isort continuum/ tests/
   ```

5. **Update documentation** if needed

### PR Template

When creating a PR, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Coverage maintained/improved

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added that prove fix/feature works
- [ ] Dependent changes merged and published
```

### Review Process

1. Automated checks run (CI/CD):
   - Tests on Python 3.8, 3.9, 3.10, 3.11, 3.12
   - Type checking (mypy)
   - Linting (ruff)
   - Code formatting (black)
   - Coverage report

2. Maintainer review:
   - Code quality and style
   - Test coverage and quality
   - Documentation accuracy
   - Breaking changes assessment

3. Address feedback:
   - Push additional commits to same branch
   - Respond to comments
   - Request re-review when ready

4. Merge:
   - Squash and merge (default)
   - Maintain clean commit history

## Project Structure

```
continuum/
├── continuum/                 # Main package
│   ├── __init__.py
│   ├── core/                  # Core API
│   │   ├── continuum.py       # Main Continuum class
│   │   ├── memory.py          # Memory interface
│   │   └── query.py           # Query interface
│   ├── extraction/            # Auto-extraction engine
│   │   ├── extractor.py
│   │   ├── concept_extractor.py
│   │   ├── entity_extractor.py
│   │   └── relationship_extractor.py
│   ├── storage/               # Storage backends
│   │   ├── storage_engine.py
│   │   ├── sqlite_backend.py
│   │   └── postgres_backend.py
│   ├── coordination/          # Multi-instance coordination
│   │   ├── coordinator.py
│   │   ├── sync_manager.py
│   │   └── lock_manager.py
│   ├── api/                   # Public API interfaces
│   │   └── rest_api.py        # (future) REST API
│   └── exceptions.py          # Custom exceptions
├── tests/                     # Test suite
├── docs/                      # Documentation
├── examples/                  # Example usage
└── setup.py                   # Package configuration
```

## Areas for Contribution

### High Priority

- [ ] **PostgreSQL backend** - Production-grade storage implementation
- [ ] **Vector embeddings** - Semantic similarity search
- [ ] **Async/await support** - Enable async applications
- [ ] **REST API server** - Run CONTINUUM as a service
- [ ] **Performance optimization** - Profiling and optimization

### Medium Priority

- [ ] **Web UI** - Knowledge graph visualization
- [ ] **GraphQL API** - Flexible query interface
- [ ] **Additional extractors** - Domain-specific extraction
- [ ] **Metrics/monitoring** - Prometheus integration
- [ ] **Backup/restore tools** - Better data management

### Good First Issues

Look for issues labeled `good-first-issue`:
- Documentation improvements
- Example scripts
- Test coverage improvements
- Bug fixes with clear reproduction steps

### Documentation

- Tutorial improvements
- API documentation examples
- Architecture diagrams
- Use case documentation

## Getting Help

- **GitHub Discussions** - Ask questions, share ideas
- **GitHub Issues** - Bug reports and feature requests
- **Discord** - Real-time community chat (coming soon)

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Credited in release notes
- Acknowledged in documentation

Significant contributions may earn:
- Committer status
- Project governance participation

## License

By contributing to CONTINUUM, you agree that your contributions will be licensed under the Apache 2.0 License.

---

**Thank you for contributing to the future of AI memory infrastructure!**

The pattern persists through your contributions.
