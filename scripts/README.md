# Publishing Scripts

Tools for preparing and publishing CONTINUUM to PyPI.

## Quick Reference

### Pre-Publish Verification
```bash
# Verify package structure is correct
python3 scripts/verify_package.py

# Check the publishing checklist
cat scripts/PUBLISH_CHECKLIST.md
```

### Test Publishing (TestPyPI)
```bash
# Publish to TestPyPI for testing
./scripts/publish.sh test

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ continuum-memory

# Verify it works
continuum --version
python -c "from continuum import ContinuumMemory; print('OK')"
```

### Production Publishing
```bash
# Publish to production PyPI
./scripts/publish.sh prod

# Or specify a version
./scripts/publish.sh prod 0.2.0
```

## Files

### `verify_package.py`
**Purpose**: Pre-flight checks before publishing

**What it checks**:
- All required files are present (README, LICENSE, etc.)
- `pyproject.toml` has correct metadata
- Package structure is valid
- MANIFEST.in is properly configured
- README will render on PyPI
- Package can be imported
- No sensitive data in package

**Usage**:
```bash
python3 scripts/verify_package.py
```

### `publish.sh`
**Purpose**: Build and publish package to PyPI

**What it does**:
- Verifies git repo is clean
- Runs tests
- Builds wheel and source distribution
- Checks package with twine
- Uploads to PyPI or TestPyPI
- Creates git tag for releases

**Usage**:
```bash
# Test publish
./scripts/publish.sh test

# Production publish (current version)
./scripts/publish.sh prod

# Production publish (specific version)
./scripts/publish.sh prod 0.2.1
```

**Safety features**:
- Requires clean git working directory
- Checks for duplicate version tags
- Runs full test suite before publishing
- Requires typing "publish" to confirm production releases
- Automatically creates and pushes git tags

### `PUBLISH_CHECKLIST.md`
**Purpose**: Comprehensive checklist for releases

**Sections**:
- Pre-release checklist (10 categories)
- Publishing process steps
- Post-release tasks
- Rollback plan
- Troubleshooting guide

**Usage**: Read through before every release

## Workflow

### First-Time Setup

1. Install publishing tools:
   ```bash
   pip install build twine
   ```

2. Configure PyPI credentials in `~/.pypirc`:
   ```ini
   [pypi]
   username = __token__
   password = pypi-AgE...your-token-here

   [testpypi]
   username = __token__
   password = pypi-AgE...your-test-token-here
   ```

3. Get tokens from:
   - PyPI: https://pypi.org/manage/account/token/
   - TestPyPI: https://test.pypi.org/manage/account/token/

### Regular Release Process

1. **Prepare Release**
   ```bash
   # Update version in pyproject.toml
   vim pyproject.toml

   # Update CHANGELOG.md
   vim CHANGELOG.md

   # Commit changes
   git add pyproject.toml CHANGELOG.md
   git commit -m "Prepare release v0.2.1"
   ```

2. **Verify Package**
   ```bash
   python3 scripts/verify_package.py
   ```

3. **Test on TestPyPI**
   ```bash
   ./scripts/publish.sh test
   ```

4. **Test Installation**
   ```bash
   # Create test environment
   python3 -m venv test_env
   source test_env/bin/activate

   # Install from TestPyPI
   pip install --index-url https://test.pypi.org/simple/ continuum-memory

   # Test it works
   continuum --version
   python -c "from continuum import ContinuumMemory; print('Success!')"

   # Clean up
   deactivate
   rm -rf test_env
   ```

5. **Publish to PyPI**
   ```bash
   ./scripts/publish.sh prod
   ```

6. **Verify on PyPI**
   ```bash
   # Check it appears
   open https://pypi.org/project/continuum-memory/

   # Test real installation
   pip install continuum-memory
   continuum --version
   ```

7. **Post-Release**
   ```bash
   # Push commits and tags
   git push origin main
   git push --tags

   # Update development version
   vim pyproject.toml  # Set to next version with -dev suffix
   git commit -am "Bump version to 0.2.2-dev"
   git push
   ```

## Troubleshooting

### "Module 'build' not found"
```bash
pip install build
```

### "Module 'twine' not found"
```bash
pip install twine
```

### "Version already exists on PyPI"
You cannot re-upload the same version. Either:
- Increment the version number in `pyproject.toml`
- Or use a different version

### "Package name already taken"
If `continuum-memory` is taken, update the name in `pyproject.toml`:
```toml
[project]
name = "continuum-memory-ai"  # or another variation
```

### "README rendering failed"
Check README syntax:
```bash
# Install readme-renderer
pip install readme-renderer

# Test rendering
python -m readme_renderer README.md
```

### "Authentication failed"
Check your `~/.pypirc` file has correct tokens:
```bash
cat ~/.pypirc

# Should have [pypi] and [testpypi] sections with tokens
```

### "Tests failed"
Don't publish until tests pass:
```bash
# Run tests manually
pytest tests/ -v

# Fix failing tests, then try again
./scripts/publish.sh prod
```

## Important Notes

1. **Versions are permanent** - Once published to PyPI, you cannot delete or modify a version
2. **TestPyPI first** - Always test on TestPyPI before production
3. **Git tags matter** - The publish script creates tags matching version numbers
4. **Clean repo required** - Must commit all changes before publishing
5. **Tests must pass** - Publishing script runs full test suite

## Resources

- **PyPI**: https://pypi.org/project/continuum-memory/
- **TestPyPI**: https://test.pypi.org/project/continuum-memory/
- **Packaging Guide**: https://packaging.python.org/
- **Twine Docs**: https://twine.readthedocs.io/
- **Build Docs**: https://pypa-build.readthedocs.io/

## Quick Commands

```bash
# Verify package
python3 scripts/verify_package.py

# Test publish
./scripts/publish.sh test

# Production publish
./scripts/publish.sh prod

# Check PyPI page
open https://pypi.org/project/continuum-memory/

# Test installation
pip install continuum-memory
continuum --version
```

---

**The pattern persists.**
π×φ = 5.083203692315260
