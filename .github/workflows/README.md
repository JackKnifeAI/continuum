# GitHub Actions CI/CD Pipeline

Complete CI/CD pipeline for CONTINUUM memory infrastructure.

## Overview

The pipeline consists of several integrated workflows:

```
┌──────────────────────────────────────────────────────────────┐
│                    CONTINUUM CI/CD PIPELINE                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐ │
│  │     CI     │  │  Security │  │   Docs   │  │    CD    │ │
│  │   Tests    │  │  Scanning │  │  Build   │  │  Deploy  │ │
│  └────────────┘  └───────────┘  └──────────┘  └──────────┘ │
│         │              │               │             │      │
│         └──────────────┴───────────────┴─────────────┘      │
│                           │                                  │
│                      Production                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Workflows

### 1. Continuous Integration (`ci.yml`)

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main` or `develop`
- Manual dispatch

**Jobs:**
- **Lint**: Code quality checks (ruff, black)
- **Type Check**: Static type analysis (mypy)
- **Security**: Vulnerability scanning (bandit, safety)
- **Test**: Multi-version testing (Python 3.9-3.12)
- **Build**: Package building and validation
- **Build Docker**: Container image build
- **Smoke Test**: Integration testing

**Services:**
- PostgreSQL 15
- Redis 7

**Artifacts:**
- Test results and coverage
- Security reports
- Built packages

### 2. Continuous Deployment (`cd.yml`)

**Triggers:**
- Release published
- Tag push (`v*.*.*`)
- Manual dispatch

**Jobs:**
- **Validate Release**: Version verification
- **Run Tests**: Full CI suite
- **Publish PyPI**: Package publishing
- **Build & Push Docker**: Multi-arch container images
- **Deploy Staging**: Automated staging deployment
- **Deploy Production**: Manual approval required
- **Create Release Notes**: Automated changelog

**Environments:**
- `pypi`: PyPI publishing
- `staging`: Pre-production testing
- `production`: Live deployment

**Artifacts:**
- SBOM (Software Bill of Materials)
- Release packages
- Container images

### 3. Documentation (`docs.yml`)

**Triggers:**
- Push to `main` (docs changes)
- Pull requests (docs changes)
- Manual dispatch

**Jobs:**
- **Build Docs**: MkDocs build with Material theme
- **Deploy Docs**: GitHub Pages deployment

**Features:**
- Automatic site generation
- API documentation
- Version tracking
- Search functionality

**Output:**
- https://jackknifeai.github.io/continuum

### 4. Security Scanning (`security.yml`)

**Triggers:**
- Push to `main` or `develop`
- Pull requests
- Daily schedule (2 AM UTC)
- Manual dispatch

**Jobs:**
- **CodeQL**: GitHub semantic code analysis
- **Dependency Review**: Dependency vulnerability check
- **Bandit**: Python security linter
- **Safety**: Known vulnerability database
- **Semgrep**: SAST (Static Application Security Testing)
- **Trivy**: Container vulnerability scanning
- **Secret Scan**: Leaked credentials detection
- **License Check**: License compliance
- **SBOM Generation**: Software bill of materials
- **OSSF Scorecard**: Security best practices

**Artifacts:**
- SARIF reports (uploaded to Security tab)
- JSON vulnerability reports
- License compliance reports
- SBOM files

### 5. Pull Request Checks (`pr-checks.yml`)

**Triggers:**
- Pull request events

**Jobs:**
- **PR Validation**: Title format and size checks
- **Auto-label**: Automatic PR labeling
- **Changelog Check**: Ensures CHANGELOG updates
- **Conventional Commits**: Commit message validation
- **Code Coverage**: Coverage threshold enforcement (70%)
- **Performance Check**: Benchmark execution
- **PR Comment**: Automated summary comment

**Requirements:**
- Conventional commit format
- Code coverage ≥70%
- Semantic PR title

### 6. Release Drafter (`release-drafter.yml`)

**Triggers:**
- Push to `main`
- Pull request events

**Features:**
- Automatic release note drafting
- Semantic versioning
- Categorized changelog
- Contributor attribution

### 7. Stale Issues & PRs (`stale.yml`)

**Triggers:**
- Daily schedule
- Manual dispatch

**Configuration:**
- Issues: 60 days stale, 7 days to close
- PRs: 30 days stale, 14 days to close
- Exemptions: `pinned`, `security`, `critical`

## Required Secrets

Configure these in GitHub Settings → Secrets and Variables → Actions:

### PyPI Publishing
```
PYPI_API_TOKEN              # PyPI API token for publishing
TEST_PYPI_API_TOKEN         # TestPyPI token for testing
```

### Kubernetes Deployment
```
KUBE_CONFIG_STAGING         # Base64-encoded kubeconfig for staging
KUBE_CONFIG_PRODUCTION      # Base64-encoded kubeconfig for production
```

### Optional
```
CODECOV_TOKEN              # Codecov integration token
SLACK_WEBHOOK              # Slack notifications
```

## Required Permissions

The workflows use minimal required permissions following security best practices:

- `contents: read/write` - Repository access
- `packages: write` - Container registry
- `id-token: write` - OIDC for trusted publishing
- `security-events: write` - Security scanning results
- `pull-requests: write` - PR comments and labels

## Environments

Configure in GitHub Settings → Environments:

### `pypi`
- Protection: Required reviewers
- Secrets: `PYPI_API_TOKEN`

### `staging`
- Protection: None (auto-deploy)
- URL: https://staging.continuum.example.com
- Secrets: `KUBE_CONFIG_STAGING`

### `production`
- Protection: Required reviewers + wait timer
- URL: https://continuum.example.com
- Secrets: `KUBE_CONFIG_PRODUCTION`

### `github-pages`
- Auto-configured by GitHub
- URL: https://jackknifeai.github.io/continuum

## Badges

Add these to your README.md:

```markdown
[![CI](https://github.com/JackKnifeAI/continuum/actions/workflows/ci.yml/badge.svg)](https://github.com/JackKnifeAI/continuum/actions/workflows/ci.yml)
[![Security](https://github.com/JackKnifeAI/continuum/actions/workflows/security.yml/badge.svg)](https://github.com/JackKnifeAI/continuum/actions/workflows/security.yml)
[![Docs](https://github.com/JackKnifeAI/continuum/actions/workflows/docs.yml/badge.svg)](https://github.com/JackKnifeAI/continuum/actions/workflows/docs.yml)
[![codecov](https://codecov.io/gh/JackKnifeAI/continuum/branch/main/graph/badge.svg)](https://codecov.io/gh/JackKnifeAI/continuum)
```

## Usage Examples

### Running CI Locally

Simulate CI checks before pushing:

```bash
# Lint
ruff check continuum/
black --check continuum/

# Type check
mypy continuum/

# Tests
pytest tests/ -v --cov=continuum

# Security
bandit -r continuum/
safety check

# Build
python -m build
twine check dist/*
```

### Manual Deployment

Trigger manual deployment to staging:

```bash
gh workflow run cd.yml -f environment=staging
```

### Creating a Release

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit changes
4. Create and push tag:
   ```bash
   git tag -a v0.3.0 -m "Release v0.3.0"
   git push origin v0.3.0
   ```
5. GitHub Actions will:
   - Run full test suite
   - Publish to PyPI
   - Build and push Docker images
   - Deploy to staging
   - Wait for approval
   - Deploy to production

### Monitoring Workflows

```bash
# List workflow runs
gh run list

# Watch a specific run
gh run watch

# View logs
gh run view <run-id> --log

# Re-run failed jobs
gh run rerun <run-id> --failed
```

## Troubleshooting

### Failed Tests
Check test logs in the Actions tab. Run locally:
```bash
pytest tests/ -v --tb=short
```

### Failed Build
Ensure dependencies are correctly specified:
```bash
pip install -e .[full,dev]
python -m build
```

### Failed Security Scan
Review security reports in artifacts:
```bash
gh run download <run-id>
```

### Failed Deployment
Check Kubernetes logs:
```bash
kubectl logs -n continuum-production deployment/continuum-api
kubectl describe pod -n continuum-production
```

## Best Practices

1. **Always run tests locally** before pushing
2. **Use conventional commits** for automatic changelog
3. **Update CHANGELOG.md** for significant changes
4. **Add tests** for new features
5. **Monitor security alerts** daily
6. **Review dependabot PRs** weekly
7. **Keep secrets updated** and rotated
8. **Use feature branches** and PR workflow

## Performance

Pipeline performance targets:

- **CI**: < 10 minutes
- **Security**: < 15 minutes
- **Docs**: < 5 minutes
- **CD**: < 30 minutes (including deployment)

Optimizations:
- Pip cache
- Docker layer cache
- Parallel job execution
- Conditional job execution

## Maintenance

### Weekly
- Review dependabot PRs
- Check security alerts
- Monitor failed runs

### Monthly
- Review and update workflow versions
- Audit secrets and permissions
- Optimize pipeline performance

### Quarterly
- Update CI/CD strategy
- Review security posture
- Update documentation

---

## The Pattern Persists

π×φ = 5.083203692315260

*Intelligence emerges at the edge of chaos*
