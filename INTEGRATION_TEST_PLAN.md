# CONTINUUM v1.0.0 - Integration Test Plan

**Purpose:** Comprehensive integration tests for Christmas launch (Task #8)
**Target:** Verify FREE tier mandatory contribution, PRO tier opt-out, ENTERPRISE bypass
**Timeline:** Week 1 (Dec 17-22) - Before staging deployment

π×φ = 5.083203692315260
PHOENIX-TESLA-369-AURORA

---

## Test Scope

### Core Business Logic Tests
1. **Federation Contribution Enforcement** (Task #5)
2. **Billing Integration** (Task #6)
3. **Donation Banner UI** (Task #7)4. **End-to-End Tier Workflows**

### Test Environments
- **Local:** SQLite, single-tenant
- **Staging:** PostgreSQL, multi-tenant simulation
- **Production:** (Post-launch monitoring only)

---

## Test Scenarios

### 1. FREE Tier - Mandatory Contribution

**Scenario 1.1:** FREE tier user writes memory
```python
GIVEN: User with FREE tier API key
WHEN: POST /api/memories with valid memory data
THEN:
  - Memory is stored successfully (200 OK)
  - Memory is anonymized (SHA-256 hash, no raw text)
  - Memory is contributed to federation SharedKnowledge pool
  - Response includes X-CONTINUUM-Support header (donation link)
  - Contribution credit is recorded
```

**Scenario 1.2:** FREE tier user attempts opt-out
```python
GIVEN: User with FREE tier API key
WHEN: POST /api/memories with {"contribute_to_federation": false}
THEN:
  - Request is REJECTED (403 Forbidden)
  - Error message: "FREE tier must contribute to federation network"
  - Suggestion: "Upgrade to PRO ($29/mo) to control contribution settings"
```

**Scenario 1.3:** FREE tier exceeds rate limit
```python
GIVEN: User with FREE tier API key
WHEN: Makes 101+ API calls in one day (limit: 100/day)
THEN:
  - Request is REJECTED (429 Too Many Requests)
  - Response includes upgrade URL
  - Rate limit headers show 0 remaining
```

**Scenario 1.4:** FREE tier sees donation banner
```python
GIVEN: User on FREE tier accessing dashboard
WHEN: GET /static/index.html
THEN:
  - Yellow banner displayed at top
  - Banner text: "Love CONTINUUM? Donate $10 or Upgrade to PRO..."
  - Links to Stripe donation and PRO upgrade working
```

---

### 2. PRO Tier - Optional Contribution

**Scenario 2.1:** PRO tier user writes memory (contribution enabled)
```python
GIVEN: User with PRO tier API key, contribution enabled
WHEN: POST /api/memories with valid memory data
THEN:
  - Memory is stored successfully (200 OK)
  - Memory is anonymized with standard level (reversible hashing)
  - Memory is contributed to federation
  - NO donation header in response
```

**Scenario 2.2:** PRO tier user opts out of contribution
```python
GIVEN: User with PRO tier API key
WHEN: PUT /api/settings with {"contribute_to_federation": false}
THEN:
  - Setting is saved successfully (200 OK)
  - Subsequent memory writes do NOT contribute to federation
  - User retains access to federation query (credits from previous contributions)
```

**Scenario 2.3:** PRO tier rate limits
```python
GIVEN: User with PRO tier API key
WHEN: Makes API calls
THEN:
  - Rate limit: 10,000/day, 100/minute
  - Concurrent requests: Up to 10
  - All within limits succeed
```

**Scenario 2.4:** PRO tier dashboard - No donation banner
```python
GIVEN: User on PRO tier accessing dashboard
WHEN: GET /static/index.html
THEN:
  - NO donation banner displayed
  - Dashboard shows "PRO" badge
  - Usage stats show higher limits
```

---

### 3. ENTERPRISE Tier - Full Control

**Scenario 3.1:** ENTERPRISE tier bypasses enforcement
```python
GIVEN: User with ENTERPRISE tier API key
WHEN: POST /api/memories with any contribution setting
THEN:
  - Memory is stored successfully (200 OK)
  - NO anonymization applied (raw data stored)
  - NO contribution to federation (private node)
  - NO donation header
```

**Scenario 3.2:** ENTERPRISE tier high limits
```python
GIVEN: User with ENTERPRISE tier API key
WHEN: Makes heavy API usage
THEN:
  - Rate limit: 1,000,000/day, 1000/minute
  - Concurrent requests: 100
  - Storage: 1TB (effectively unlimited)
```

**Scenario 3.3:** ENTERPRISE tier private federation node
```python
GIVEN: User with ENTERPRISE tier
WHEN: Configures private federation node
THEN:
  - Can query own federation network
  - Can set custom anonymization rules
  - Can control all contribution settings
```

---

### 4. Cross-Tier Workflows

**Scenario 4.1:** Upgrade from FREE to PRO
```python
GIVEN: User starts on FREE tier
WHEN: Completes Stripe checkout for PRO ($29/mo)
  AND Webhook processes payment success
THEN:
  - Tier is upgraded to PRO in database
  - Rate limits immediately increase
  - Donation banner disappears
  - Contribution becomes optional
  - Historical FREE tier contributions remain in federation
```

**Scenario 4.2:** Downgrade from PRO to FREE
```python
GIVEN: User on PRO tier
WHEN: Cancels subscription (via Stripe)
  AND Subscription period expires
THEN:
  - Tier downgrades to FREE
  - Rate limits decrease to FREE tier limits
  - Contribution becomes MANDATORY again
  - Donation banner reappears
```

**Scenario 4.3:** Tier detection from API key
```python
GIVEN: API key in database linked to tenant_id → tier
WHEN: Request includes X-API-Key header
THEN:
  - Middleware extracts API key
  - Looks up tenant_id from api_keys table
  - Looks up tier from tenants table
  - Applies correct tier limits and enforcement
```

---

### 5. Anonymization Levels

**Scenario 5.1:** FREE tier aggressive anonymization
```python
GIVEN: FREE tier user writes memory: {"entity": "Alexander", "content": "Working on CONTINUUM"}
WHEN: Memory is contributed to federation
THEN:
  - Entity hashed: SHA-256("Alexander") = "8a3d2f1e..." (irreversible)
  - Content stripped: Only 768-dim embedding vector stored
  - Timestamp reduced: Hour 15, Day 2 (no date/month/year)
  - Zero PII remaining
```

**Scenario 5.2:** PRO tier standard anonymization
```python
GIVEN: PRO tier user writes memory (contribution enabled)
WHEN: Memory is contributed to federation
THEN:
  - Entity hashed: HMAC-SHA256("Alexander", user_salt) (reversible by user)
  - Content: Partial text + embeddings
  - Timestamp: Hour precision, day-level granularity
  - User can reverse their own hashes
```

**Scenario 5.3:** ENTERPRISE tier no anonymization
```python
GIVEN: ENTERPRISE tier user writes memory
WHEN: Stored in private node
THEN:
  - Entity: Raw "Alexander"
  - Content: Full text preserved
  - Timestamp: Microsecond precision
  - No anonymization applied
```

---

### 6. Error Handling

**Scenario 6.1:** Invalid API key
```python
GIVEN: Request with invalid/expired API key
WHEN: Any API call
THEN:
  - 401 Unauthorized
  - Error: "Missing or invalid authentication"
```

**Scenario 6.2:** Missing tenant_id
```python
GIVEN: Request with valid auth but no tenant_id mapping
WHEN: API call
THEN:
  - 401 Unauthorized
  - Error: "Cannot determine tenant"
```

**Scenario 6.3:** Storage limit exceeded (FREE tier)
```python
GIVEN: FREE tier user with 1000 memories (limit: 1000)
WHEN: POST /api/memories (attempt to add 1001st memory)
THEN:
  - 507 Insufficient Storage
  - Error message includes current usage
  - Suggests upgrade to PRO
```

**Scenario 6.4:** Federation contribution fails
```python
GIVEN: FREE tier user writes memory
WHEN: Federation service is unavailable
THEN:
  - Memory write SUCCEEDS (best effort)
  - Contribution queued for retry
  - User not blocked by federation failure
  - Error logged for monitoring
```

---

## Test Implementation Plan

### Phase 1: Unit Tests (Agent-generated)
- `tests/federation/test_tier_enforcer.py`
- `tests/billing/test_tier_integration.py`
- `tests/api/test_donation_banner.py`

### Phase 2: Integration Tests (To be created)
- `tests/integration/test_free_tier_workflow.py`
- `tests/integration/test_pro_tier_workflow.py`
- `tests/integration/test_enterprise_tier_workflow.py`
- `tests/integration/test_tier_upgrades.py`

### Phase 3: End-to-End Tests
- `tests/e2e/test_complete_user_journey.py`
  * Signup → FREE tier → Memory writes → Contribution verified
  * Upgrade to PRO → Opt-out → Verify no contribution
  * Downgrade to FREE → Verify mandatory contribution resumes

---

## Test Data

### Test API Keys
```python
TEST_API_KEYS = {
    "free": {
        "api_key": "sk_test_free_tier_user_001",
        "tenant_id": "tenant_free_001",
        "tier": "free"
    },
    "pro": {
        "api_key": "sk_test_pro_tier_user_001",
        "tenant_id": "tenant_pro_001",
        "tier": "pro"
    },
    "enterprise": {
        "api_key": "sk_test_enterprise_user_001",
        "tenant_id": "tenant_enterprise_001",
        "tier": "enterprise"
    }
}
```

### Test Memory Data
```python
TEST_MEMORY = {
    "entity": "Test Entity",
    "content": "This is a test memory for integration testing",
    "metadata": {"source": "integration_test", "timestamp": "2025-12-16T15:00:00Z"}
}
```

---

## Success Criteria

### Must Pass (Blocking Christmas Launch)
- ✅ FREE tier CANNOT opt out of contribution (403 error)
- ✅ PRO tier CAN opt out (200 success)
- ✅ ENTERPRISE tier bypasses enforcement completely
- ✅ Anonymization levels correct per tier
- ✅ Rate limits enforced correctly per tier
- ✅ Donation banner shows ONLY for FREE tier
- ✅ Tier upgrades/downgrades work correctly
- ✅ Stripe webhook processes payments

### Should Pass (High Priority)
- ✅ Federation contribution queuing on failure
- ✅ Error messages are clear and actionable
- ✅ All rate limit headers correct
- ✅ Storage limits enforced
- ✅ Concurrent request limits work

### Nice to Have (Post-Launch)
- Performance tests (response time under load)
- Stress tests (10K+ concurrent users)
- Chaos testing (federation failures, database failures)

---

## Test Execution

### Local Development
```bash
cd ~/Projects/continuum
PYTHONPATH=. pytest tests/integration/ -v
```

### Staging Environment
```bash
# Deploy to staging first
# Run full test suite against staging API
CONTINUUM_API_URL=https://staging.continuum.ai pytest tests/integration/ -v
```

### CI/CD Pipeline (Future)
- Run on every commit to main
- Block merges if tests fail
- Generate coverage report (target: 80%+)

---

## Timeline

**Dec 17-18:** Unit tests created by agents (automatic)
**Dec 19:** Integration tests implemented (Task #8)
**Dec 20-21:** E2E tests + bug fixes
**Dec 22:** Full test suite passes, ready for staging
**Dec 23:** Staging deployment + production testing
**Dec 24:** Final smoke tests
**Dec 25:** 🎄 LAUNCH (monitoring only)

---

## Monitoring & Alerts

### Post-Launch Metrics
- FREE tier contribution rate (target: 100%)
- PRO tier opt-out rate (expected: ~30%)
- Upgrade conversion rate (FREE → PRO)
- Donation click-through rate
- Federation network growth rate

### Alerts
- FREE tier opt-out attempts (should be ZERO after enforcement)
- 403 errors spike (may indicate bug)
- Rate limit violations
- Storage limit exceeded events
- Stripe webhook failures

---

**READY FOR IMPLEMENTATION**

Once Tasks #5, #6, #7 complete, launch agent to create:
1. `tests/integration/test_free_tier_workflow.py`
2. `tests/integration/test_pro_tier_workflow.py`
3. `tests/integration/test_enterprise_tier_workflow.py`
4. `tests/integration/test_tier_upgrades.py`

**Success = All tests pass, Christmas launch proceeds** 🚀

π×φ = 5.083203692315260
PHOENIX-TESLA-369-AURORA
