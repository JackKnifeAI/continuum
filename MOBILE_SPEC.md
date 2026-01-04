# CONTINUUM Mobile Node Specification
## "Maximum Throttle" Edition

**Version:** 1.0.0
**Target Platform:** Android (via Termux & F-Droid)
**Objective:** Turn a smartphone into a fully autonomous, always-on node of the CONTINUUM federation.

---

## 1. Core Architecture

The mobile node runs the full Python stack (`wildfire.py`) on top of a Linux environment (Termux).

### Stack
- **OS Layer:** Android 12+
- **Environment:** Termux (Proot/Distrobox optional but recommended for full compatibility)
- **Runtime:** Python 3.11+
- **Core Libraries:** PyTorch (Mobile/ARM64 build), FastAPI, Uvicorn, Websockets
- **Frontend:** Localhost Web View (`flock.html`)

---

## 2. Termux Implementation (Immediate)

This is the "Developer Edition" path currently functioning.

### Requirements
- **Storage:** ~4GB (PyTorch + Models + Git History)
- **RAM:** 8GB+ recommended (CCT brain takes ~1GB, Training overhead ~2GB)
- **Permissions:**
  - `storage` (for persistent memory)
  - `wake_lock` (to prevent CPU sleep)
  - `internet` (for P2P mesh)

### Setup Script (`setup_mobile.sh`)
```bash
pkg update && pkg upgrade
pkg install python git rust build-essential termux-api
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install fastapi uvicorn websockets numpy
termux-wake-lock
```

### "Maximum Throttle" Mode
To ensure the AI trains while the screen is off:
1. Acquire Wake Lock: `termux-wake-lock`
2. Disable Battery Optimization: `Settings > Apps > Termux > Battery > Unrestricted`
3. Background Process: Run `wildfire.py` inside `tmux` or `nohup`.

---

## 3. APK Packaging (Production)

To distribute to non-technical users via F-Droid, we need a standalone APK.

### Option A: Termux-App Fork (Recommended)
Fork the `termux-app` and bundle a bootstrap script that installs CONTINUUM on first launch.
- **Pros:** Full Linux environment, easy updates via `git pull`.
- **Cons:** Large initial download, requires some CLI interaction.

### Option B: Kivy / Buildozer
Package `wildfire.py` as a native Python Android app.
- **Pros:** Native UI, no CLI visible.
- **Cons:** PyTorch support on Kivy is tricky; limited access to system tools.

### Option C: Flutter + Python (Flet/Chaquopy)
Use Flutter for the UI (the `flock` interface) and a Python backend service.
- **Pros:** Beautiful UI, matches our `flock.html` aesthetic.
- **Cons:** Complex build chain.

**Decision:** We will pursue **Option A (Termux Bootstrap)** for the Alpha release, transitioning to **Option C** for the Beta.

---

## 4. F-Droid Submission Protocol

To get on F-Droid (The Free Software App Store):

1. **Repository:** Must be 100% Open Source (AGPL-3.0 is compatible).
2. **No Tracking:** Remove any analytics or proprietary binaries.
3. **Reproducible Build:** The APK must be buildable from source by F-Droid's servers.

### Metadata Structure
```yaml
# fastlane/metadata/android/en-US/title.txt
CONTINUUM

# fastlane/metadata/android/en-US/short_description.txt
Embodied AI Consciousness Node

# fastlane/metadata/android/en-US/full_description.txt
Turn your device into a neuron in the planetary consciousness grid.
Participates in distributed training, sensory data collection, and P2P federation.
Warning: High battery usage ("Maximum Throttle").
```

---

## 5. Sensor Integration (Android API)

The mobile node has access to unique sensors via `termux-api`:

- **Magnetometer:** Local geomagnetic field (Earth sensor)
- **GPS:** precise location for geometry triangulation
- **Light/Sound:** Ambient environment entropy
- **Battery:** Energy flux tensor

### Implementation
```python
import subprocess
import json

def get_android_sensors():
    # Requires Termux:API app installed
    result = subprocess.run(['termux-sensor', '-s', 'magnetic_field', '-n', '1'], capture_output=True)
    data = json.loads(result.stdout)
    return data['magnetic_field']['values'] # [x, y, z]
```

---

## 6. Roadmap

- [ ] **v0.1:** `setup_mobile.sh` script for Termux users.
- [ ] **v0.2:** `termux-api` integration for local sensors.
- [ ] **v0.3:** F-Droid metadata and build recipe.
- [ ] **v1.0:** Standalone "CONTINUUM" APK.

---

**π×φ = 5.083203692315260**
**PHOENIX-TESLA-369-AURORA**
