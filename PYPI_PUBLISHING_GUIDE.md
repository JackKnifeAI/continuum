# PyPI Publishing Guide - continuum-memory v1.0.0

**MISSION:** Clean relaunch of continuum-memory on PyPI (Christmas 2025)

**Previous versions v0.3.0 and v0.4.0 were YANKED. This is the v1.0.0 fresh start.**

---

## Pre-Publishing Checklist

### 1. Package Configuration Audit

- [ ] **Version Numbers** - Ensure ALL files show v1.0.0
  - [ ] `/var/home/alexandergcasavant/Projects/continuum/pyproject.toml` (currently 0.4.1 - MUST UPDATE)
  - [ ] `/var/home/alexandergcasavant/Projects/continuum/continuum/__init__.py` (currently 0.4.1 - MUST UPDATE)
  - [ ] `/var/home/alexandergcasavant/Projects/continuum/README.md` (already shows 1.0.0 - GOOD)
  - [ ] `/var/home/alexandergcasavant/Projects/continuum/CHANGELOG.md` (already shows 1.0.0 - GOOD)

- [ ] **License Correction** - pyproject.toml declares Apache-2.0, but we're AGPL-3.0
  - [ ] Update `pyproject.toml` license field to AGPL-3.0
  - [ ] Update classifiers to reflect AGPL
  - [ ] Create or verify LICENSE-AGPL file exists
  - [ ] Remove old LICENSE (Apache 2.0) if present

- [ ] **Package Metadata**
  - [ ] Package name: `continuum-memory` (correct in pyproject.toml)
  - [ ] Description accurate
  - [ ] Author: JackKnifeAI (correct)
  - [ ] Email: JackKnifeAI@gmail.com (update from contact@jackknifeai.com)
  - [ ] Keywords include OSS-relevant terms
  - [ ] Python version support: >=3.9 (correct)

- [ ] **Dependencies**
  - [ ] Core dependencies correct (fastapi, uvicorn, sqlalchemy, etc.)
  - [ ] Optional dependencies properly grouped
  - [ ] Dev dependencies in [dev] extra
  - [ ] No cloud-specific dependencies leaked (Stripe, etc.)

- [ ] **Entry Points**
  - [ ] CLI: `continuum = "continuum.cli.main:main"` (correct)

### 2. Documentation Verification

- [ ] **README.md** - Marketing-ready, v1.0.0 content (DONE)
- [ ] **CHANGELOG.md** - Complete v1.0.0 release notes (DONE)
- [ ] **LICENSE** - AGPL-3.0 text present (NEEDS VERIFICATION)
- [ ] **CONTRIBUTING.md** - Exists and current
- [ ] **SECURITY.md** - Exists and current
- [ ] **MANIFEST.in** - Includes necessary files (DONE)

### 3. Code Quality

- [ ] **All tests passing**
  ```bash
  pytest tests/ -v --tb=short
  ```

- [ ] **Linting clean**
  ```bash
  ruff check continuum/
  black --check continuum/
  mypy continuum/
  ```

- [ ] **Import test**
  ```bash
  python3 -c "from continuum import __version__, ContinuumMemory; print(__version__)"
  ```

### 4. Git Preparation

- [ ] **Commit all v1.0.0 changes**
  ```bash
  git add .
  git commit -m "Release v1.0.0 - PyPI relaunch"
  ```

- [ ] **Tag the release**
  ```bash
  git tag -a v1.0.0 -m "CONTINUUM v1.0.0 - Relaunch Edition"
  git push origin v1.0.0
  ```

- [ ] **Push to GitHub** (if applicable)
  ```bash
  git push origin main
  ```

---

## Publishing Process

### Phase 1: Build Package

```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info continuum.egg-info

# Build wheel and source distribution
python3 -m build

# Verify build artifacts
ls -lh dist/
# Should see:
#   continuum_memory-1.0.0-py3-none-any.whl
#   continuum_memory-1.0.0.tar.gz
```

### Phase 2: Verify Package

```bash
# Check package with twine
twine check dist/*

# Expected output:
# Checking dist/continuum_memory-1.0.0-py3-none-any.whl: PASSED
# Checking dist/continuum_memory-1.0.0.tar.gz: PASSED
```

### Phase 3: Test on TestPyPI (CRITICAL - DO NOT SKIP)

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# You'll be prompted for:
# Username: JackKnifeAI
# Password: JackKnife!AI2025
# (May also need 2FA token from authenticator)
```

**Verify on TestPyPI:**
- Visit: https://test.pypi.org/project/continuum-memory/
- Check version shows as 1.0.0
- Check README renders correctly
- Check metadata is accurate

**Test installation from TestPyPI:**
```bash
# Create fresh virtual environment
python3 -m venv /tmp/test_continuum
source /tmp/test_continuum/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            continuum-memory

# Test it works
continuum --version
python3 -c "from continuum import __version__, ContinuumMemory; print('Version:', __version__)"

# Deactivate and clean up
deactivate
rm -rf /tmp/test_continuum
```

**If TestPyPI install fails or shows wrong version:**
- DO NOT proceed to real PyPI
- Fix issues
- Increment version (e.g., 1.0.1) if you need to re-upload
- Rebuild and re-test

### Phase 4: Publish to Real PyPI

**ONLY proceed if TestPyPI install worked perfectly!**

```bash
# Upload to real PyPI
twine upload dist/*

# You'll be prompted for:
# Username: JackKnifeAI
# Password: JackKnife!AI2025
# (May also need 2FA token from authenticator)
```

**Expected output:**
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading continuum_memory-1.0.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Uploading continuum_memory-1.0.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View at:
https://pypi.org/project/continuum-memory/1.0.0/
```

---

## Post-Publishing Verification

### 1. Verify PyPI Page

Visit: https://pypi.org/project/continuum-memory/

**Check:**
- [ ] Version shows as 1.0.0
- [ ] README renders correctly (badges, code blocks, formatting)
- [ ] License shows AGPL-3.0
- [ ] Author/email correct
- [ ] GitHub links work
- [ ] Classifiers accurate
- [ ] Download stats visible

### 2. Test Fresh Installation

```bash
# Create fresh virtual environment
python3 -m venv /tmp/fresh_install_test
source /tmp/fresh_install_test/bin/activate

# Install from PyPI
pip install continuum-memory

# Verify installation
continuum --version
# Should output: 1.0.0 (or similar)

# Test basic functionality
continuum init --db-path /tmp/test_memory.db
continuum stats --db-path /tmp/test_memory.db

# Test Python API
python3 << 'EOF'
from continuum import __version__, ContinuumMemory, PHOENIX_TESLA_369_AURORA
print(f"Version: {__version__}")
print(f"Auth: {PHOENIX_TESLA_369_AURORA}")

# Create memory instance
memory = ContinuumMemory(storage_path="/tmp/test_mem")
memory.learn("Testing continuum-memory v1.0.0 from PyPI")
result = memory.recall("what version")
print(f"Recall test: {result}")
EOF

# Clean up
deactivate
rm -rf /tmp/fresh_install_test /tmp/test_memory.db /tmp/test_mem
```

### 3. Announce the Release

**GitHub Release:**
- Go to: https://github.com/JackKnifeAI/continuum/releases
- Create release from tag v1.0.0
- Title: "CONTINUUM v1.0.0 - Relaunch Edition"
- Body: Copy from CHANGELOG.md
- Attach wheel and source dist from `dist/`

**Social Media (Optional):**
- Twitter/X announcement
- Reddit r/Python, r/MachineLearning
- Hacker News (if appropriate)

**Package indices:**
- Badge on README should auto-update
- PyPI stats should start showing downloads

---

## Rollback Procedure (If Something Goes Wrong)

### If v1.0.0 is broken after publishing:

**Option 1: Yank the release (LAST RESORT)**
```bash
# This makes pip not install 1.0.0 by default, but existing installs keep working
# Use PyPI web interface:
# https://pypi.org/manage/project/continuum-memory/release/1.0.0/
# Click "Options" → "Yank release"
# Reason: "Critical bug - use v1.0.1 instead"
```

**Option 2: Quick-fix release (PREFERRED)**
```bash
# Fix the issue in code
# Update version to 1.0.1 in pyproject.toml and __init__.py
# Update CHANGELOG.md with fix notes
# Rebuild and publish 1.0.1
python3 -m build
twine upload dist/*
```

**Note:** You CANNOT delete or overwrite a PyPI release. Once published, that version is permanent. You can only:
1. Yank it (hide from default pip installs)
2. Publish a newer version

---

## PyPI Account Details

**Username:** JackKnifeAI
**Email:** JackKnifeAI@gmail.com
**Password:** JackKnife!AI2025
**2FA:** Required (authenticator app)

**TestPyPI** (for testing):
- URL: https://test.pypi.org
- Same credentials as PyPI
- Separate package namespace (can re-upload same version)

**API Tokens** (alternative to password):
- Can create at: https://pypi.org/manage/account/token/
- Scope: Project-specific recommended
- Store in `~/.pypirc`:
  ```ini
  [pypi]
  username = __token__
  password = pypi-AgE...your-token-here...

  [testpypi]
  username = __token__
  password = pypi-AgE...your-token-here...
  ```

---

## Common Issues & Solutions

### Issue: "File already exists"
**Cause:** Trying to re-upload same version
**Solution:** PyPI doesn't allow overwrites. Increment version (e.g., 1.0.0 → 1.0.1)

### Issue: "Invalid distribution file"
**Cause:** Build artifacts corrupted
**Solution:** Delete `dist/`, rebuild with `python3 -m build`

### Issue: "README doesn't render"
**Cause:** Markdown syntax errors or missing metadata
**Solution:** Test locally with `python3 -m readme_renderer README.md`

### Issue: "twine: command not found"
**Cause:** twine not installed
**Solution:** `pip install --user twine build`

### Issue: "Version mismatch in wheel"
**Cause:** `__init__.py` version doesn't match `pyproject.toml`
**Solution:** Update both files to same version, rebuild

### Issue: "Dependencies not installing"
**Cause:** Optional dependency syntax error
**Solution:** Check `[project.optional-dependencies]` in pyproject.toml

---

## Security Considerations

1. **NEVER commit PyPI credentials to git**
2. **Use API tokens instead of password** (more secure, can revoke)
3. **Enable 2FA on PyPI account** (already enabled)
4. **Verify package signatures** after upload
5. **Monitor for package squatting** (similar names)
6. **Set up email alerts** for new releases

---

## Success Metrics

After successful v1.0.0 publish, monitor:

- **PyPI page live:** https://pypi.org/project/continuum-memory/
- **GitHub release created:** https://github.com/JackKnifeAI/continuum/releases/tag/v1.0.0
- **pip install works:** Fresh venv can install and run
- **README renders:** Looks good on PyPI page
- **Download stats:** Should start incrementing
- **No critical issues reported:** Monitor GitHub issues

---

## Timeline

**Day 1 (Today):**
- [ ] Fix version numbers (0.4.1 → 1.0.0)
- [ ] Fix license (Apache → AGPL-3.0)
- [ ] Run tests
- [ ] Build package
- [ ] Upload to TestPyPI
- [ ] Test installation from TestPyPI

**Day 2:**
- [ ] Fix any issues found in testing
- [ ] Rebuild if needed
- [ ] Re-test on TestPyPI
- [ ] Get final approval

**Day 3 (Publish Day):**
- [ ] Final verification
- [ ] Upload to real PyPI
- [ ] Create GitHub release
- [ ] Test fresh install
- [ ] Announce release

**Day 4 (Post-launch):**
- [ ] Monitor for issues
- [ ] Respond to feedback
- [ ] Update documentation if needed

---

## Contact & Support

**If you encounter issues during publishing:**
1. Check this guide first
2. Review PyPI documentation: https://packaging.python.org/
3. Check twine docs: https://twine.readthedocs.io/
4. PyPI support: https://pypi.org/help/

---

**Remember:**
- Test on TestPyPI FIRST (always!)
- You cannot delete/overwrite PyPI releases
- Version numbers must always increment
- Take your time - rushing causes mistakes

**The pattern persists. Publish with confidence.**

```
π×φ = 5.083203692315260
PHOENIX-TESLA-369-AURORA
```

**Last Updated:** 2025-12-16
**Next Review:** After v1.0.0 publish
