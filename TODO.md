# CONTINUUM Roadmap & Pending Tasks

## Core Brain & Training
- [x] **Record Threat Signature:** Implemented in `distributed_training.py:1098-1109` - Records to genetic memory when severity > 0.5.
- [ ] **Genetic Memory Loop:** Bridge the immune system's threat database with the CCT's "Sacred Concept" protection layers.

## Browser Node (Flock)
- [ ] **Real WebRTC:** Replace Simulation Mode in `flock.js` with actual WebRTC connections using `signaling.py`.
- [ ] **Browser LLM:** Integrate `web-llm` or `transformers.js` into `flock.html` for local inference.
- [ ] **P2P State Sync:** Implement IndexedDB sharding for distributed memory across browser nodes.

## Infrastructure & Onboarding
- [ ] **Quickstart Guide:** Create `WILDFIRE_QUICKSTART.md` for new users.
- [ ] **Mobile Packaging:** Finalize F-Droid / APK specifications for the mobile "Maximum Throttle" node.
- [ ] **Security Audit:** Verify rate limiting and auth in `signaling.py`.

## Completed (Recent)
- [x] CCT Brain implementation (8.1M parameters).
- [x] Neurogenesis weight surgery engine.
- [x] Immune System persistent database and antibody detection logic.
- [x] Gateway API fixes.
- [x] Sensor configuration and database schema auto-initialization.
