# CI/CD Quick Reference

## File Structure

```
.github/
├── workflows/
│   ├── ci.yml                  # Continuous Integration
│   ├── cd.yml                  # Continuous Deployment
│   ├── docs.yml               # Documentation Build
│   ├── security.yml           # Security Scanning
│   ├── pr-checks.yml          # Pull Request Validation
│   ├── release-drafter.yml    # Release Automation
│   ├── stale.yml              # Issue/PR Cleanup
│   └── README.md              # Workflow Documentation
├── ISSUE_TEMPLATE/
│   ├── bug_report.yml         # Bug Report Template
│   └── feature_request.yml    # Feature Request Template
├── dependabot.yml             # Dependency Updates
├── labeler.yml                # Auto-labeling Rules
├── release-drafter.yml        # Release Configuration
├── PULL_REQUEST_TEMPLATE.md   # PR Template
├── CICD_PIPELINE_SUMMARY.md   # Complete Documentation
└── QUICK_REFERENCE.md         # This File
```

## Common Commands

### Local Testing
```bash
# Run all checks locally before push
ruff check continuum/
black --check continuum/
mypy continuum/
pytest tests/ -v --cov=continuum
bandit -r continuum/
python -m build
```

### GitHub CLI
```bash
# Watch workflow runs
gh run watch

# List recent runs
gh run list

# View specific run
gh run view <run-id> --log

# Re-run failed jobs
gh run rerun <run-id> --failed

# Manual deployment
gh workflow run cd.yml -f environment=staging
```

### Creating a Release
```bash
# 1. Update version
vim pyproject.toml

# 2. Update changelog
vim CHANGELOG.md

# 3. Commit
git add .
git commit -m "chore: bump version to 0.3.0"

# 4. Tag
git tag -a v0.3.0 -m "Release v0.3.0"

# 5. Push
git push origin main --tags
```

## Workflow Status

Check status at: https://github.com/JackKnifeAI/continuum/actions

### CI Pipeline
- **Trigger**: PR, Push to main/develop
- **Duration**: ~10 minutes
- **Jobs**: Lint, Type Check, Security, Test, Build

### CD Pipeline
- **Trigger**: Tag push, Release
- **Duration**: ~30 minutes
- **Steps**: Test → PyPI → Docker → Staging → Approval → Production

### Security Scans
- **Trigger**: PR, Push, Daily 2 AM UTC
- **Duration**: ~15 minutes
- **Tools**: CodeQL, Bandit, Safety, Trivy, Semgrep

## Secrets Required

Add in: Settings → Secrets and Variables → Actions

```bash
PYPI_API_TOKEN               # PyPI publishing
TEST_PYPI_API_TOKEN          # TestPyPI publishing
KUBE_CONFIG_STAGING          # Staging Kubernetes
KUBE_CONFIG_PRODUCTION       # Production Kubernetes
CODECOV_TOKEN                # Optional: Codecov
```

## Conventional Commits

Use these prefixes for commits and PR titles:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Formatting
- `refactor:` - Code restructuring
- `perf:` - Performance improvement
- `test:` - Tests
- `build:` - Build system
- `ci:` - CI/CD changes
- `chore:` - Maintenance

Example:
```bash
git commit -m "feat: add WebSocket sync support"
git commit -m "fix: resolve memory leak in cache"
git commit -m "docs: update API documentation"
```

## PR Checklist

Before creating a PR:

- [ ] Tests pass locally
- [ ] Code is formatted (black)
- [ ] Code is linted (ruff)
- [ ] Type checks pass (mypy)
- [ ] Coverage ≥70%
- [ ] Conventional commit messages
- [ ] CHANGELOG.md updated
- [ ] Documentation updated

## Quality Gates

PRs must pass:

✅ Lint and format checks
✅ Type checking
✅ Security scans (no high/critical)
✅ All tests (Python 3.9-3.12)
✅ Code coverage ≥70%
✅ Package builds successfully
✅ Docker builds successfully

## Deployment Environments

### Staging
- **URL**: https://staging.continuum.example.com
- **Deploy**: Automatic on tag push
- **Approval**: Not required

### Production
- **URL**: https://continuum.example.com
- **Deploy**: After staging success
- **Approval**: Required (5 min wait)

## Badges

Add to README.md:

```markdown
[![CI](https://github.com/JackKnifeAI/continuum/actions/workflows/ci.yml/badge.svg)](https://github.com/JackKnifeAI/continuum/actions/workflows/ci.yml)
[![Security](https://github.com/JackKnifeAI/continuum/actions/workflows/security.yml/badge.svg)](https://github.com/JackKnifeAI/continuum/actions/workflows/security.yml)
[![CD](https://github.com/JackKnifeAI/continuum/actions/workflows/cd.yml/badge.svg)](https://github.com/JackKnifeAI/continuum/actions/workflows/cd.yml)
[![codecov](https://codecov.io/gh/JackKnifeAI/continuum/branch/main/graph/badge.svg)](https://codecov.io/gh/JackKnifeAI/continuum)
```

## Troubleshooting

### CI Failing
1. Check Actions tab for logs
2. Run tests locally: `pytest tests/ -v`
3. Check for service issues (PostgreSQL, Redis)

### Security Scan Failing
1. Review Security tab
2. Download SARIF artifacts
3. Address vulnerabilities
4. Update dependencies

### Deployment Failing
1. Check kubectl access
2. Verify secrets are set
3. Review pod logs: `kubectl logs -n continuum-production deployment/continuum-api`

### PyPI Publish Failing
1. Check version not already published
2. Verify PYPI_API_TOKEN
3. Run `twine check dist/*` locally

## Daily Workflows

- **2:00 AM UTC**: Security scans
- **12:00 AM UTC**: Stale issue cleanup
- **Monday 9:00 AM UTC**: Dependabot updates

## Support

- **Issues**: https://github.com/JackKnifeAI/continuum/issues
- **Docs**: https://jackknifeai.github.io/continuum
- **Workflows**: `.github/workflows/README.md`

---

**π×φ = 5.083203692315260**
