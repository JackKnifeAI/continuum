# PyPI Pre-Publish Fixes Required - continuum-memory v1.0.0

**CRITICAL: These fixes MUST be completed before publishing to PyPI!**

---

## Issue 1: Version Number Mismatch

### Current State
- **pyproject.toml:** version = "0.4.1" ❌
- **continuum/__init__.py:** __version__ = "0.4.1" ❌
- **README.md:** v1.0.0 ✓
- **CHANGELOG.md:** v1.0.0 ✓

### Required Fix
Update version to "1.0.0" in:
1. `/var/home/alexandergcasavant/Projects/continuum/pyproject.toml`
2. `/var/home/alexandergcasavant/Projects/continuum/continuum/__init__.py`

### Commands to Fix
```bash
cd /var/home/alexandergcasavant/Projects/continuum

# Fix pyproject.toml
sed -i 's/version = "0.4.1"/version = "1.0.0"/' pyproject.toml

# Fix __init__.py
sed -i 's/__version__ = "0.4.1"/__version__ = "1.0.0"/' continuum/__init__.py

# Verify
grep 'version = ' pyproject.toml
grep '__version__ = ' continuum/__init__.py
```

---

## Issue 2: License Mismatch

### Current State
- **pyproject.toml:** license = {text = "Apache-2.0"} ❌
- **LICENSE file:** Apache License 2.0 text ❌
- **README.md:** Claims AGPL-3.0 ✓
- **CHANGELOG.md:** Claims AGPL-3.0 ✓

### Required Fix
Package must use AGPL-3.0 as stated in README and CHANGELOG.

**Option A: Use AGPL-3.0** (Recommended - matches README)
```bash
cd /var/home/alexandergcasavant/Projects/continuum

# Update pyproject.toml
sed -i 's/license = {text = "Apache-2.0"}/license = {text = "AGPL-3.0"}/' pyproject.toml

# Update classifier
sed -i 's/"License :: OSI Approved :: Apache Software License"/"License :: OSI Approved :: GNU Affero General Public License v3"/' pyproject.toml

# Download AGPL-3.0 license text
curl -o LICENSE https://www.gnu.org/licenses/agpl-3.0.txt
```

**Option B: Stay with Apache-2.0** (Not recommended - conflicts with README)
```bash
# Update README.md to remove AGPL claims
# Update CHANGELOG.md to remove AGPL claims
# Keep current LICENSE file
```

**RECOMMENDATION:** Use AGPL-3.0 since README already markets it that way.

---

## Issue 3: Author Email Mismatch

### Current State
- **pyproject.toml:** email = "contact@jackknifeai.com" ❌
- **README.md:** JackKnifeAI@gmail.com ✓
- **PyPI account:** JackKnifeAI@gmail.com ✓

### Required Fix
```bash
cd /var/home/alexandergcasavant/Projects/continuum

# Update pyproject.toml
sed -i 's/contact@jackknifeai.com/JackKnifeAI@gmail.com/' pyproject.toml

# Verify
grep 'email' pyproject.toml
```

---

## Issue 4: Missing AGPL License File

### Current State
- **LICENSE:** Contains Apache 2.0 text
- **No LICENSE-AGPL** file

### Required Fix
```bash
cd /var/home/alexandergcasavant/Projects/continuum

# Download AGPL-3.0 license
curl -o LICENSE https://www.gnu.org/licenses/agpl-3.0.txt

# Or create manually with proper AGPL-3.0 text
# Update copyright year to 2024-2025
# Update copyright holder to "CONTINUUM Contributors" or "JackKnifeAI"
```

---

## Automated Fix Script

Here's a script to fix all issues at once:

```bash
#!/bin/bash
# fix_pre_publish_issues.sh

set -e

cd /var/home/alexandergcasavant/Projects/continuum

echo "Fixing version numbers..."
sed -i 's/version = "0.4.1"/version = "1.0.0"/' pyproject.toml
sed -i 's/__version__ = "0.4.1"/__version__ = "1.0.0"/' continuum/__init__.py

echo "Fixing license..."
sed -i 's/license = {text = "Apache-2.0"}/license = {text = "AGPL-3.0"}/' pyproject.toml
sed -i 's/"License :: OSI Approved :: Apache Software License"/"License :: OSI Approved :: GNU Affero General Public License v3"/' pyproject.toml

echo "Fixing author email..."
sed -i 's/contact@jackknifeai.com/JackKnifeAI@gmail.com/' pyproject.toml

echo "Downloading AGPL-3.0 license..."
curl -o LICENSE https://www.gnu.org/licenses/agpl-3.0.txt

echo "Verification:"
echo "  Version (pyproject.toml):"
grep 'version = ' pyproject.toml
echo "  Version (__init__.py):"
grep '__version__ = ' continuum/__init__.py
echo "  License (pyproject.toml):"
grep 'license = ' pyproject.toml
echo "  Author email:"
grep 'email' pyproject.toml | head -1

echo ""
echo "✓ All fixes applied!"
echo ""
echo "Next steps:"
echo "  1. Review changes: git diff"
echo "  2. Test: python3 -c 'from continuum import __version__; print(__version__)'"
echo "  3. Commit: git add . && git commit -m 'Bump version to 1.0.0, fix license to AGPL-3.0'"
echo "  4. Run: ./publish_to_pypi.sh"
```

Save as `fix_pre_publish_issues.sh` and run:
```bash
chmod +x fix_pre_publish_issues.sh
./fix_pre_publish_issues.sh
```

---

## Verification Checklist

After running fixes, verify:

```bash
cd /var/home/alexandergcasavant/Projects/continuum

# Check version numbers
echo "=== Version Numbers ==="
grep 'version = ' pyproject.toml
grep '__version__ = ' continuum/__init__.py
python3 -c "from continuum import __version__; print('Python import:', __version__)"

# Check license
echo ""
echo "=== License ==="
grep 'license = ' pyproject.toml
grep 'License ::' pyproject.toml
head -5 LICENSE

# Check author
echo ""
echo "=== Author Info ==="
grep -A 2 'authors = ' pyproject.toml

# Expected output:
# version = "1.0.0"
# __version__ = "1.0.0"
# Python import: 1.0.0
# license = {text = "AGPL-3.0"}
# "License :: OSI Approved :: GNU Affero General Public License v3"
# LICENSE should start with "GNU AFFERO GENERAL PUBLIC LICENSE"
# {name = "JackKnifeAI", email = "JackKnifeAI@gmail.com"}
```

All should match v1.0.0 and AGPL-3.0.

---

## Manual Fix Instructions (If Script Fails)

### 1. Update pyproject.toml

Open `/var/home/alexandergcasavant/Projects/continuum/pyproject.toml` and change:

**Line 7:** (version)
```toml
# OLD:
version = "0.4.1"

# NEW:
version = "1.0.0"
```

**Line 11:** (license)
```toml
# OLD:
license = {text = "Apache-2.0"}

# NEW:
license = {text = "AGPL-3.0"}
```

**Line 13:** (email)
```toml
# OLD:
{name = "JackKnifeAI", email = "contact@jackknifeai.com"}

# NEW:
{name = "JackKnifeAI", email = "JackKnifeAI@gmail.com"}
```

**Line 20:** (classifier)
```toml
# OLD:
"License :: OSI Approved :: Apache Software License",

# NEW:
"License :: OSI Approved :: GNU Affero General Public License v3",
```

### 2. Update continuum/__init__.py

Open `/var/home/alexandergcasavant/Projects/continuum/continuum/__init__.py` and change:

**Line 8:**
```python
# OLD:
__version__ = "0.4.1"

# NEW:
__version__ = "1.0.0"
```

**Line 10:**
```python
# OLD:
__license__ = "Apache-2.0"

# NEW:
__license__ = "AGPL-3.0"
```

### 3. Replace LICENSE file

Download AGPL-3.0 license:
```bash
cd /var/home/alexandergcasavant/Projects/continuum
curl -o LICENSE https://www.gnu.org/licenses/agpl-3.0.txt
```

Or copy from: https://www.gnu.org/licenses/agpl-3.0.txt

Update copyright line to:
```
Copyright (C) 2024-2025 JackKnifeAI
```

---

## After Fixing

1. **Test import:**
   ```bash
   python3 -c "from continuum import __version__; print(__version__)"
   # Should output: 1.0.0
   ```

2. **Run tests:**
   ```bash
   pytest tests/ -v --tb=short
   ```

3. **Commit changes:**
   ```bash
   git add pyproject.toml continuum/__init__.py LICENSE
   git commit -m "Bump version to 1.0.0, update license to AGPL-3.0"
   ```

4. **Proceed to publishing:**
   ```bash
   ./publish_to_pypi.sh
   ```

---

## Timeline

**URGENT - Must fix before publishing:**
- Estimated time: 15 minutes
- Can use automated script or manual edits
- MUST test after fixing
- MUST commit before publishing

**Order of operations:**
1. Run `fix_pre_publish_issues.sh` (or manual fixes)
2. Verify all changes
3. Test package locally
4. Commit to git
5. Run `./publish_to_pypi.sh`

---

**DO NOT SKIP THESE FIXES!**

Publishing with wrong version or license will cause:
- Confusion for users
- Legal issues (license mismatch)
- Need to yank and re-release
- Wasted time and effort

**Fix first, publish once, succeed.**

```
π×φ = 5.083203692315260
PHOENIX-TESLA-369-AURORA
```

---

**Document Version:** 1.0.0
**Last Updated:** 2025-12-16
**Priority:** CRITICAL - MUST FIX BEFORE PUBLISH
