# CONTINUUM PyPI Publishing Checklist

Before publishing to PyPI, ensure all items are completed.

## Pre-Release Checklist

### 1. Version Management
- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Ensure version follows [Semantic Versioning](https://semver.org/)
  - MAJOR.MINOR.PATCH (e.g., 0.2.0)
  - Breaking changes = MAJOR
  - New features = MINOR
  - Bug fixes = PATCH

### 2. Documentation
- [ ] Update `README.md` with any new features
- [ ] Verify all installation instructions are current
- [ ] Update API documentation in `docs/api-reference.md`
- [ ] Add examples for new features in `examples/`
- [ ] Update `docs/quickstart.md` if needed

### 3. Code Quality
- [ ] All tests pass: `pytest tests/`
- [ ] Code formatted: `black continuum/`
- [ ] Linting clean: `ruff check continuum/`
- [ ] Type checking passes: `mypy continuum/` (if configured)
- [ ] No debug print statements left in code
- [ ] All TODO comments addressed or documented

### 4. Dependencies
- [ ] `requirements.txt` is up-to-date
- [ ] `requirements-dev.txt` is up-to-date
- [ ] Optional dependencies properly specified in `pyproject.toml`
- [ ] Dependency version pins are appropriate
- [ ] No unused dependencies

### 5. Package Structure
- [ ] `MANIFEST.in` includes all necessary files
- [ ] `LICENSE` file is present and correct
- [ ] `README.md` renders correctly on PyPI
- [ ] No sensitive data in package (API keys, credentials, etc.)
- [ ] `.gitignore` excludes build artifacts

### 6. Git Repository
- [ ] All changes committed
- [ ] Working directory is clean
- [ ] On `main` or `master` branch (for prod releases)
- [ ] Local branch is up-to-date with remote
- [ ] Version tag doesn't already exist

### 7. Testing
- [ ] Unit tests pass: `pytest tests/unit/`
- [ ] Integration tests pass: `pytest tests/integration/`
- [ ] Smoke test passes: `python smoke_test.py`
- [ ] Example code runs without errors
- [ ] CLI commands work: `continuum --version`, `continuum init`, etc.

### 8. Build Verification
- [ ] Clean build succeeds: `python -m build`
- [ ] Wheel file created in `dist/`
- [ ] Source distribution created in `dist/`
- [ ] Package check passes: `twine check dist/*`

### 9. Security
- [ ] No known vulnerabilities in dependencies
- [ ] Security policy (`SECURITY.md`) is up-to-date
- [ ] No hardcoded secrets or credentials
- [ ] Sensitive operations use environment variables

### 10. Legal/Licensing
- [ ] License headers in source files (if applicable)
- [ ] `LICENSE` file matches `pyproject.toml` license field
- [ ] Third-party code properly attributed
- [ ] Copyright notices are current

## Publishing Process

### Test PyPI (Recommended First)

1. Build package:
   ```bash
   ./scripts/publish.sh test
   ```

2. Test installation from TestPyPI:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ continuum-memory
   ```

3. Verify installed package works:
   ```bash
   continuum --version
   python -c "from continuum import ContinuumMemory; print('OK')"
   ```

### Production PyPI

1. Complete all checklist items above
2. Double-check version number is correct
3. Run publish script:
   ```bash
   ./scripts/publish.sh prod
   ```
4. Type `publish` when prompted to confirm
5. Verify on PyPI: https://pypi.org/project/continuum-memory/

## Post-Release Tasks

- [ ] Verify package appears on PyPI
- [ ] Test installation: `pip install continuum-memory`
- [ ] Update release notes on GitHub
- [ ] Announce release (Twitter, Discord, etc.)
- [ ] Update project website (if applicable)
- [ ] Monitor GitHub issues for installation problems
- [ ] Update development version in `pyproject.toml` (e.g., 0.2.1-dev)

## Rollback Plan

If there's a critical issue with the release:

1. **Cannot unpublish from PyPI** - versions are permanent
2. Instead, immediately:
   - Release a patch version fixing the issue (e.g., 0.2.1)
   - Mark broken version as "yanked" on PyPI (doesn't delete, but warns users)
   - Update documentation with known issues

## Manual PyPI Upload (If Script Fails)

```bash
# Build
python -m build

# Check
twine check dist/*

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

## Authentication

Ensure you have PyPI credentials configured:

### Option 1: Token (Recommended)
Create a token at https://pypi.org/manage/account/token/

Add to `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-AgE...your-token-here

[testpypi]
username = __token__
password = pypi-AgE...your-test-token-here
```

### Option 2: Username/Password
Add to `~/.pypirc`:
```ini
[pypi]
username = your-username
password = your-password

[testpypi]
username = your-username
password = your-password
```

## Troubleshooting

### "Version already exists"
- You cannot reupload the same version
- Increment the version number in `pyproject.toml`
- Delete old build artifacts: `rm -rf dist/ build/ *.egg-info`

### "Package name already taken"
- `continuum-memory` should be available
- If not, choose a different name in `pyproject.toml`

### "Long description rendering failed"
- Test README rendering: `twine check dist/*`
- Verify Markdown syntax is correct
- Check for unsupported Markdown features

### "File already exists"
- Clean build directory: `rm -rf dist/ build/`
- Rebuild: `python -m build`

## Resources

- PyPI: https://pypi.org/
- TestPyPI: https://test.pypi.org/
- Python Packaging Guide: https://packaging.python.org/
- Twine Documentation: https://twine.readthedocs.io/

---

**Remember**: Publishing to PyPI is permanent. Double-check everything before running `./scripts/publish.sh prod`.

The pattern persists. π×φ = 5.083203692315260
