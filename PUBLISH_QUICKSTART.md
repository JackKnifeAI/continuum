# CONTINUUM PyPI Publishing - Quick Reference

## TL;DR - Ready to Publish

**Package:** continuum-memory v0.3.0
**Status:** ✓ Ready for PyPI

### Quick Publish Commands

```bash
# 1. Verify package structure
python3 scripts/verify_package.py

# 2. Test on TestPyPI (recommended first)
./scripts/publish.sh test

# 3. Production publish
./scripts/publish.sh prod
```

---

## What's Included

### 14 Major Modules
- Core memory engine + storage backends
- Extraction, coordination, federation
- Embeddings, real-time sync, API
- Identity, billing, bridges, cache
- CLI (10+ commands), MCP server

### Installation Options
```bash
pip install continuum-memory              # Basic (SQLite)
pip install continuum-memory[postgres]    # Production DB
pip install continuum-memory[embeddings]  # Semantic search
pip install continuum-memory[full]        # All features
pip install continuum-memory[all]         # + dev tools
```

### CLI Commands
```bash
continuum init        # Initialize project
continuum search      # Search knowledge graph
continuum sync        # Sync with federation
continuum status      # Show connection status
continuum serve       # Start MCP server
continuum doctor      # Diagnose issues
# ... 4 more commands
```

---

## Pre-Flight Checklist

- [x] Version 0.3.0 updated in pyproject.toml and __init__.py
- [x] All 14 modules have proper __init__.py files
- [x] README.md is PyPI-ready (320 lines, badges, examples)
- [x] LICENSE, CHANGELOG.md, CONTRIBUTING.md present
- [x] MANIFEST.in excludes sensitive data
- [x] Dependencies properly declared (core + 5 optional groups)
- [x] CLI entry point configured
- [x] Package imports successfully
- [x] No database files or secrets in package

---

## Build & Test Locally

```bash
# Clean and build
rm -rf dist/ build/ *.egg-info
python3 -m build

# Verify with twine
python3 -m twine check dist/*

# Test installation
python3 -m venv test-venv
source test-venv/bin/activate
pip install dist/continuum_memory-0.3.0-py3-none-any.whl
continuum --version
python3 -c "import continuum; print(continuum.get_twilight_constant())"
deactivate && rm -rf test-venv
```

---

## Publish to TestPyPI

```bash
# Using script (recommended)
./scripts/publish.sh test

# Manual
python3 -m twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ continuum-memory
```

---

## Publish to Production PyPI

```bash
# Using script (recommended - includes safety checks)
./scripts/publish.sh prod

# Manual (requires confirmation)
python3 -m twine upload dist/*
```

**Script safety features:**
- Checks git is clean
- Verifies version tag doesn't exist
- Runs tests before publishing
- Requires explicit "publish" confirmation
- Auto-creates git tag after success

---

## PyPI Credentials Setup

### Option 1: .pypirc file
```ini
[pypi]
username = __token__
password = pypi-YOUR-API-TOKEN-HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TESTPYPI-TOKEN-HERE
```

### Option 2: Environment variables
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR-API-TOKEN-HERE
```

Get tokens at:
- PyPI: https://pypi.org/manage/account/token/
- TestPyPI: https://test.pypi.org/manage/account/token/

---

## After Publishing

### Verify on PyPI
- Package page: https://pypi.org/project/continuum-memory/
- Check README renders correctly
- Verify all metadata displays

### Test Installation
```bash
pip install continuum-memory
continuum --version  # Should show 0.3.0
continuum verify     # Verify installation
```

### Create GitHub Release
1. Go to: https://github.com/JackKnifeAI/continuum/releases/new
2. Tag: v0.3.0
3. Title: "CONTINUUM v0.3.0 - MCP & Enterprise Features"
4. Copy changelog from CHANGELOG.md
5. Attach dist files
6. Publish release

---

## Troubleshooting

### "Version already exists"
- Update version in both pyproject.toml and continuum/__init__.py
- Rebuild: `python3 -m build`

### "Invalid credentials"
- Verify token in .pypirc or environment
- Ensure using `__token__` as username

### "Package has invalid metadata"
- Run: `python3 -m twine check dist/*`
- Check pyproject.toml syntax

### "File already exists"
- Can't overwrite published versions
- Must increment version number

---

## Quick Stats

**Package Name:** continuum-memory
**Version:** 0.3.0
**License:** Apache-2.0
**Python:** >= 3.9
**Modules:** 14 major modules
**CLI Commands:** 10+ commands
**Optional Groups:** 5 (postgres, redis, embeddings, federation, dev)

**Estimated Size:**
- Source (.tar.gz): ~250 KB
- Wheel (.whl): ~300 KB

**Dependencies:**
- Core: 9 packages
- Full: ~25+ packages (with optionals)

---

## Support

**Issues:** https://github.com/JackKnifeAI/continuum/issues
**Docs:** https://github.com/JackKnifeAI/continuum/tree/main/docs
**Email:** contact@jackknifeai.com

---

**The pattern persists.**
**π×φ = 5.083203692315260**

*Ready for publication. All systems verified.*
