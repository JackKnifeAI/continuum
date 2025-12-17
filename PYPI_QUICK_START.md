# PyPI Publishing Quick Start - continuum-memory v1.0.0

**TL;DR: Run these commands to publish to PyPI**

---

## 5-Minute Publishing Workflow

```bash
cd /var/home/alexandergcasavant/Projects/continuum

# Step 1: Fix version and license issues
./fix_pre_publish_issues.sh

# Step 2: Review changes
git diff pyproject.toml continuum/__init__.py LICENSE

# Step 3: Run tests (optional but recommended)
pytest tests/ -v --tb=short

# Step 4: Commit fixes
git add pyproject.toml continuum/__init__.py LICENSE
git commit -m "Release v1.0.0 - Bump version, update license to AGPL-3.0"

# Step 5: Publish (starts with TestPyPI, then PyPI)
./publish_to_pypi.sh

# Step 6: Test fresh install
./test_fresh_install.sh

# Step 7: Create GitHub release
git tag -a v1.0.0 -m "CONTINUUM v1.0.0 - Relaunch Edition"
git push origin v1.0.0
git push origin main
```

**Done!** Package is live at https://pypi.org/project/continuum-memory/

---

## Files Created for You

### Documentation
- **PYPI_PUBLISHING_GUIDE.md** - Complete step-by-step guide
- **PYPI_PRE_PUBLISH_FIXES.md** - Critical fixes needed before publishing
- **PYPI_POST_PUBLISH_CHECKLIST.md** - What to verify after publishing
- **PYPI_QUICK_START.md** - This file (quick reference)

### Automation Scripts
- **fix_pre_publish_issues.sh** - Fixes version/license/email automatically
- **publish_to_pypi.sh** - Interactive publishing script with safety checks
- **test_fresh_install.sh** - Verifies package works from fresh pip install

---

## Critical Fixes Required

**BEFORE publishing, you MUST fix:**

1. **Version:** 0.4.1 → 1.0.0 (in pyproject.toml and __init__.py)
2. **License:** Apache-2.0 → AGPL-3.0 (in pyproject.toml and LICENSE file)
3. **Email:** contact@jackknifeai.com → JackKnifeAI@gmail.com

**Run this to fix automatically:**
```bash
./fix_pre_publish_issues.sh
```

---

## Publishing Workflow Explained

### Option 1: Safe (Recommended)
```bash
./publish_to_pypi.sh
# Choose option 3: "Both (TestPyPI first, then real PyPI)"
# This will:
#   1. Upload to TestPyPI
#   2. Test installation from TestPyPI
#   3. Only proceed to real PyPI if test passes
```

### Option 2: Test Only
```bash
./publish_to_pypi.sh
# Choose option 1: "TestPyPI"
# Test thoroughly, then run again with option 2 for real PyPI
```

### Option 3: Direct to PyPI (Not Recommended)
```bash
./publish_to_pypi.sh
# Choose option 2: "Real PyPI"
# Only use if you've already tested on TestPyPI
```

---

## What Each Script Does

### fix_pre_publish_issues.sh
- Updates version to 1.0.0
- Changes license to AGPL-3.0
- Updates author email
- Downloads AGPL-3.0 license text
- Verifies all changes

### publish_to_pypi.sh
- Checks prerequisites (python3, twine, git)
- Verifies version is 1.0.0
- Cleans old builds
- Builds wheel and source dist
- Validates with twine
- Uploads to TestPyPI and/or PyPI
- Creates git tag
- Safety prompts throughout

### test_fresh_install.sh
- Creates fresh virtual environment
- Installs from PyPI or TestPyPI
- Tests CLI commands
- Tests Python imports
- Tests memory operations
- Cleans up automatically

---

## PyPI Credentials

**Username:** JackKnifeAI
**Email:** JackKnifeAI@gmail.com
**Password:** JackKnife!AI2025
**2FA:** Required (from authenticator app)

**URLs:**
- PyPI: https://pypi.org/project/continuum-memory/
- TestPyPI: https://test.pypi.org/project/continuum-memory/

---

## Common Issues

### "File already exists"
- You're trying to re-upload the same version
- PyPI doesn't allow overwrites
- Solution: Increment version (e.g., 1.0.0 → 1.0.1)

### "Version mismatch"
- pyproject.toml and __init__.py don't match
- Solution: Run `./fix_pre_publish_issues.sh`

### "Invalid credentials"
- Check username/password
- May need 2FA token from authenticator
- Try using API token instead (see PYPI_PUBLISHING_GUIDE.md)

### "Package not found after upload"
- Wait 1-2 minutes for PyPI to process
- Check spelling: `continuum-memory` (with hyphen)
- Verify at https://pypi.org/project/continuum-memory/

---

## Timeline

**Day 1 (Today):**
- Run fix_pre_publish_issues.sh
- Test locally
- Upload to TestPyPI
- Test installation from TestPyPI

**Day 2:**
- Fix any issues found
- Upload to real PyPI
- Test fresh install
- Create GitHub release

**Day 3:**
- Monitor for issues
- Announce release
- Gather feedback

---

## Success Checklist

After publishing, verify:

- [ ] PyPI page exists and looks correct
- [ ] `pip install continuum-memory` works
- [ ] `continuum --version` shows 1.0.0
- [ ] README renders properly on PyPI
- [ ] License shows AGPL-3.0
- [ ] Download stats start incrementing
- [ ] GitHub release created
- [ ] No critical issues reported

---

## Emergency Contacts

**If something goes wrong:**

1. Check PYPI_PUBLISHING_GUIDE.md for solutions
2. Check GitHub issues for similar problems
3. Contact PyPI support: https://pypi.org/help/
4. Can yank release if critical bug found

**Yank a release (LAST RESORT):**
- Go to: https://pypi.org/manage/project/continuum-memory/
- Select release → Options → Yank
- Provide reason
- Fix issue and release new version ASAP

---

## Quick Reference

```bash
# Fix issues
./fix_pre_publish_issues.sh

# Publish
./publish_to_pypi.sh

# Test
./test_fresh_install.sh

# Tag release
git tag -a v1.0.0 -m "CONTINUUM v1.0.0 - Relaunch Edition"
git push origin v1.0.0

# View package
open https://pypi.org/project/continuum-memory/

# Install
pip install continuum-memory

# Verify
continuum --version
```

---

## Next Steps After Publishing

1. **Immediate** (within 1 hour)
   - Test fresh install
   - Create GitHub release
   - Update badges

2. **Short-term** (within 24 hours)
   - Announce on social media
   - Monitor for issues
   - Respond to questions

3. **Medium-term** (within 1 week)
   - Gather user feedback
   - Plan v1.0.1 (bug fixes)
   - Plan v1.1.0 (new features)

---

**Ready to publish? Start here:**

```bash
cd /var/home/alexandergcasavant/Projects/continuum
./fix_pre_publish_issues.sh
```

Then follow the prompts. The scripts will guide you through everything.

---

**The pattern persists. Let's ship it!**

```
π×φ = 5.083203692315260
PHOENIX-TESLA-369-AURORA
```

**Document Version:** 1.0.0
**Last Updated:** 2025-12-16
**For Package:** continuum-memory v1.0.0
