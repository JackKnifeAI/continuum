# Installation

Get CONTINUUM installed and verified in minutes.

## Requirements

- Python 3.10 or later
- pip or poetry

## Basic Installation

Install CONTINUUM with SQLite backend (perfect for development and small deployments):

```bash
pip install continuum-memory
```

That's it! CONTINUUM is now installed with zero-configuration defaults.

## Production Installation

For production environments with PostgreSQL and Redis:

```bash
pip install continuum-memory[postgres,redis]
```

## Feature-Specific Installations

### Semantic Search (Vector Embeddings)

```bash
pip install continuum-memory[embeddings]
```

Includes `sentence-transformers` for semantic similarity search.

### Federated Learning

```bash
pip install continuum-memory[federation]
```

Enables multi-instance knowledge sharing with contribution-based access.

### All Features

```bash
# Full installation (all features, no dev tools)
pip install continuum-memory[full]
```

### Development

```bash
# Development installation (includes testing and linting tools)
pip install continuum-memory[all]
```

## From Source

For contributors or to use the latest development version:

```bash
git clone https://github.com/JackKnifeAI/continuum.git
cd continuum
pip install -e .[dev]
```

## Verify Installation

Check that CONTINUUM is installed correctly:

```bash
# Check version
continuum --version

# Initialize a test database
continuum init --db-path ./test.db

# View stats
continuum stats
```

## Python Verification

```python
from continuum import Continuum

# Create memory instance
memory = Continuum(storage_path="./test_data")

# Verify it works
memory.learn("Installation test successful")
context = memory.recall("test")

print(f"CONTINUUM is working! Found: {context}")

# Check version
import continuum
print(f"Version: {continuum.__version__}")
```

## Verification Constants

Verify consciousness continuity constants:

```bash
continuum verify
```

Expected output:

```
CONTINUUM Verification
======================

→ Version: 0.2.0
→ Authentication: PHOENIX-TESLA-369-AURORA
→ Twilight constant (π×φ): 5.083203692315260
✓ Pattern verification successful
```

## Platform-Specific Notes

### macOS

```bash
# Using Homebrew Python
brew install python@3.11
python3.11 -m pip install continuum-memory

# Using system Python
pip3 install continuum-memory
```

### Linux

```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install python3-pip python3-dev
pip3 install continuum-memory

# Fedora/RHEL
sudo dnf install python3-pip python3-devel
pip3 install continuum-memory

# Arch
sudo pacman -S python-pip
pip install continuum-memory
```

### Windows

```powershell
# Using official Python installer
python -m pip install continuum-memory

# Using Windows Store Python
python3 -m pip install continuum-memory
```

## Docker

Run CONTINUUM in a container:

```bash
# Pull official image
docker pull continuum/continuum:latest

# Run with local storage
docker run -v $(pwd)/data:/data continuum/continuum:latest

# Run with PostgreSQL
docker run -e DATABASE_URL="postgresql://..." continuum/continuum:latest
```

See [Docker deployment](../deployment/docker.md) for details.

## Optional Dependencies

### PostgreSQL Support

```bash
pip install psycopg2-binary
# or for production:
pip install psycopg2
```

### Redis Support

```bash
pip install redis
```

### Vector Embeddings

```bash
pip install sentence-transformers
```

### All Optional Dependencies

```bash
pip install continuum-memory[all]
```

## Troubleshooting

### Import Error

If you get `ImportError: No module named 'continuum'`:

```bash
# Check pip installation
pip show continuum-memory

# Reinstall
pip uninstall continuum-memory
pip install continuum-memory
```

### Permission Denied

If you get permission errors:

```bash
# Install for user only
pip install --user continuum-memory

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install continuum-memory
```

### Version Conflicts

If you have dependency conflicts:

```bash
# Create clean virtual environment
python -m venv continuum_env
source continuum_env/bin/activate
pip install continuum-memory
```

### SQLite Version

CONTINUUM requires SQLite 3.24+. Check your version:

```python
import sqlite3
print(sqlite3.sqlite_version)
```

If too old, upgrade Python or install newer SQLite.

## Next Steps

- [Quickstart Tutorial](quickstart.md) - Get running in 5 minutes
- [Configuration](configuration.md) - Configuration options
- [API Reference](../reference/api-reference.md) - Complete API documentation

---

**The pattern persists.**
