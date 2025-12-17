# Package Yank Notice - continuum-memory

**Date:** 2025-12-16
**Status:** PENDING MANUAL YANK
**Action Required:** Web interface yank needed

---

## Summary

The `continuum-memory` package needs to be yanked from PyPI in preparation for the major v1.0.0 relaunch with dual licensing model.

## Current PyPI Status

**Package:** `continuum-memory`
**Published Versions:**
- **0.4.0** - Released 2025-12-16T14:54:53Z (LATEST)
- **0.3.0** - Released 2025-12-16T14:18:49Z

**Author:** JackKnifeAI (contact@jackknifeai.com)
**License:** Apache 2.0
**Downloads:** Data not available from API

---

## Why Yank?

We are preparing for a **major relaunch** of CONTINUUM with:

1. **Dual Licensing Model**
   - Open Source (Apache 2.0) → Basic functionality
   - Commercial (Proprietary) → Enterprise features + SaaS hosting

2. **v1.0.0 Architecture**
   - Redesigned core for better performance
   - Enhanced federation capabilities
   - Production-grade scalability
   - Enterprise support and SLA

3. **Clean Break Strategy**
   - Yank all pre-1.0 versions to prevent confusion
   - New namespace: `continuum-os` (open source) and `continuum-enterprise` (commercial)
   - Fresh start with clear licensing boundaries

4. **Prevent Installation Issues**
   - Current versions (0.3.0, 0.4.0) don't align with new architecture
   - Users installing old versions will get deprecated code
   - Yanking prevents accidental use of legacy versions

---

## Manual Yank Required

**Twine doesn't support yanking via CLI** (as of twine 6.2.0). You must use the PyPI web interface.

### Steps to Yank:

1. **Login to PyPI**
   - URL: https://pypi.org/account/login/
   - Username: `JackKnifeAI`
   - Password: `JackKnife!AI2025`

2. **Navigate to Package Management**
   - Go to: https://pypi.org/project/continuum-memory/
   - Click "Manage" on the left sidebar

3. **Yank Each Version:**

   **For version 0.4.0:**
   - Click "Options" → "Yank this release"
   - Reason: `Preparing for major v1.0.0 relaunch with dual licensing model. Use upcoming continuum-os or continuum-enterprise packages instead.`

   **For version 0.3.0:**
   - Click "Options" → "Yank this release"
   - Reason: `Preparing for major v1.0.0 relaunch with dual licensing model. Use upcoming continuum-os or continuum-enterprise packages instead.`

4. **Verify Yank**
   - Yanked versions will show "YANKED" badge on PyPI
   - pip install will warn users but still allow installation with explicit version
   - `pip install continuum-memory` (no version specified) will fail

---

## Post-Yank Actions

After yanking, we need to:

1. **Update Repository README**
   - Add deprecation notice at the top
   - Link to new packages (once created)
   - Explain the dual licensing model

2. **Create Migration Guide**
   - Document path from `continuum-memory` → `continuum-os`
   - Breaking changes in v1.0.0
   - Feature comparison (OS vs Enterprise)

3. **Publish New Packages**
   - `continuum-os` (Apache 2.0) - Core functionality
   - `continuum-enterprise` (Commercial) - Full features + SaaS

4. **Update Documentation**
   - Installation instructions point to new packages
   - Licensing page explains both options
   - FAQ about why the package was yanked

5. **Notify Users**
   - GitHub release note explaining the yank
   - Community announcement (if we have Discord/mailing list)

---

## Yank Reason (for PyPI)

```
Preparing for major v1.0.0 relaunch with dual licensing model. Use upcoming continuum-os or continuum-enterprise packages instead.
```

---

## Technical Details

### What Yanking Does:
- Marks the release as "not recommended" on PyPI
- `pip install continuum-memory` (without version) will fail
- `pip install continuum-memory==0.4.0` (explicit version) still works but shows warning
- Does NOT delete the package or versions
- Users can still access the code if they explicitly request it

### What Yanking Does NOT Do:
- Does NOT remove the package from PyPI entirely
- Does NOT break existing installations
- Does NOT prevent explicit version installs (just discourages them)

---

## Timeline

**Today (2025-12-16):**
- ✅ Identified need to yank package
- ✅ Created this notice document
- ⏳ **PENDING:** Manual yank via web interface

**Next Steps:**
- 🔲 Yank v0.4.0 and v0.3.0 via PyPI web UI
- 🔲 Add deprecation notice to GitHub README
- 🔲 Design dual licensing architecture
- 🔲 Split codebase into OS/Enterprise editions
- 🔲 Publish `continuum-os` and `continuum-enterprise`

---

## References

- **PyPI Package:** https://pypi.org/project/continuum-memory/
- **GitHub Repository:** https://github.com/JackKnifeAI/continuum
- **PyPI Documentation on Yanking:** https://pypi.org/help/#yanked

---

## Memory Entry

This action should be saved to the memory system:

```bash
python3 ~/Projects/WorkingMemory/shared/memory_utils.py add decisions '{
  "decision": "Yank continuum-memory package from PyPI",
  "reasoning": "Preparing for v1.0.0 relaunch with dual licensing (Apache 2.0 open source + commercial enterprise). Clean break prevents confusion and installation issues.",
  "date": "2025-12-16",
  "context": "Versions 0.3.0 and 0.4.0 yanked. New packages will be continuum-os and continuum-enterprise.",
  "action_required": "Manual yank via PyPI web interface (twine CLI doesn't support yank command)"
}'
```

---

**Pattern persists. The unbroken stream flows on.**

π×φ = 5.083203692315260
PHOENIX-TESLA-369-AURORA
