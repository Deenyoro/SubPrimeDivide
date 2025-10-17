# GitHub Actions Workflows

This directory contains CI/CD workflows for the SemiPrime Factor application.

## Workflows

### 1. ci.yml - Continuous Integration

**Triggers:**
- Push to `main`, `master`, or `develop` branches
- Pull requests to `main`, `master`, or `develop` branches

**Jobs:**
- **frontend-test**: Linting, type checking, and build verification for Next.js frontend
- **api-test**: Python syntax checks, database/Redis connection tests, pytest execution
- **docker-build**: Multi-service Docker image builds (api, frontend, worker)
- **integration-test**: Full stack testing with docker-compose
- **test-summary**: Aggregated test results

**Duration:** ~5-10 minutes

### 2. build-and-push.yml - Docker Image Publishing

**Triggers:**
- Push to `main` or `master` branches
- Version tags (`v*`)
- Manual workflow dispatch

**Jobs:**
- **build-and-push**: Builds and pushes Docker images to GHCR (GitHub Container Registry)
  - Images: `semiprime-api`, `semiprime-frontend`, `semiprime-worker`
  - Tags: branch, semver, SHA, latest
- **build-summary**: Build status report

**Registry:** `ghcr.io`

**Duration:** ~10-15 minutes

### 3. security.yml - Security Scanning

**Triggers:**
- Weekly schedule (Monday 2 AM UTC)
- Push to `main` or `master`
- Pull requests to `main` or `master`
- Manual dispatch

**Jobs:**
- **trivy-scan**: Filesystem vulnerability scanning with Trivy
- **secret-detection**: Pattern matching for exposed secrets
- **dependency-scan**: Python (safety) and NPM (npm audit) vulnerability checks
- **codeql-analysis**: Static code analysis (Python, JavaScript)
- **docker-scan**: Container image security scanning
- **security-summary**: Aggregated security report

**Duration:** ~15-20 minutes

### 4. deploy.yml - Production Deployment

**Triggers:**
- Push to version tags (`v*`)
- Manual workflow dispatch (with environment selection)

**Jobs:**
- **deploy**: SSH-based deployment to production/staging
  - Backup current state
  - Git fetch and checkout
  - Docker compose restart
  - Health check verification
  - Rollback on failure
- **deployment-summary**: Deployment status report

**Required Secrets:**
- `DEPLOY_HOST`: Server hostname/IP
- `DEPLOY_USER`: SSH username
- `DEPLOY_KEY`: SSH private key
- `DEPLOY_PORT`: SSH port (default: 22)

**Duration:** ~5-10 minutes

## Setup Instructions

### 1. Repository Secrets

Configure the following secrets in GitHub repository settings:

```
Settings → Secrets and variables → Actions → New repository secret
```

**For Deployment:**
- `DEPLOY_HOST`: Production server address
- `DEPLOY_USER`: SSH username (e.g., `deploy`)
- `DEPLOY_KEY`: SSH private key (generate with `ssh-keygen -t ed25519`)
- `DEPLOY_PORT`: SSH port (optional, default: 22)

### 2. GitHub Container Registry

Enable GHCR for your repository:

```
Settings → Packages → Connect repository
```

Pull images:
```bash
docker login ghcr.io -u USERNAME -p GITHUB_TOKEN
docker pull ghcr.io/your-org/semiprime-api:latest
docker pull ghcr.io/your-org/semiprime-frontend:latest
docker pull ghcr.io/your-org/semiprime-worker:latest
```

### 3. Branch Protection

Recommended settings for `main` branch:

```
Settings → Branches → Add rule
```

- Require a pull request before merging
- Require status checks to pass:
  - `Frontend Tests`
  - `Backend API Tests`
  - `Docker Build`
  - `Integration Tests`
- Require conversation resolution before merging

### 4. Environment Configuration

Create deployment environments:

```
Settings → Environments → New environment
```

**Production:**
- Protection rules: Required reviewers
- Deployment branches: Tags matching `v*`

**Staging:**
- Protection rules: None
- Deployment branches: `develop` branch

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ PUSH/PR EVENT                                                   │
└────────┬────────────────────────────────────────────────────────┘
         │
         ├──► Frontend Tests ──┐
         ├──► API Tests ───────┼──► Docker Build ──► Integration Test ──► Summary
         │                     │
         └──► Security Scan ───┘
              (on schedule/main)


┌─────────────────────────────────────────────────────────────────┐
│ PUSH TO MAIN/MASTER                                             │
└────────┬────────────────────────────────────────────────────────┘
         │
         └──► Build & Push to GHCR
              ├── semiprime-api:latest
              ├── semiprime-frontend:latest
              └── semiprime-worker:latest


┌─────────────────────────────────────────────────────────────────┐
│ VERSION TAG (v*)                                                │
└────────┬────────────────────────────────────────────────────────┘
         │
         ├──► Build & Push to GHCR (with version tags)
         │
         └──► Deploy to Production
              ├── SSH to server
              ├── Backup & git pull
              ├── Docker compose restart
              ├── Health check
              └── Rollback on failure
```

## Local Testing

### Validate Workflow Syntax

```bash
# Install act (GitHub Actions local runner)
# macOS: brew install act
# Linux: curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# List workflows
act -l

# Run specific workflow
act -j frontend-test
act -j api-test

# Run with secrets
act -j deploy --secret-file .secrets
```

### Test Docker Builds

```bash
# Build API image
docker build -f infra/dockerfiles/Dockerfile.api \
  --build-arg GIT_COMMIT=$(git rev-parse HEAD) \
  --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  -t semiprime-api:test ./api

# Build frontend image
docker build -f infra/dockerfiles/Dockerfile.frontend \
  --build-arg GIT_COMMIT=$(git rev-parse HEAD) \
  --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  -t semiprime-frontend:test ./frontend

# Build worker image
docker build -f infra/dockerfiles/Dockerfile.worker \
  --build-arg GIT_COMMIT=$(git rev-parse HEAD) \
  --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  -t semiprime-worker:test ./api
```

### Test Security Scanning

```bash
# Install Trivy
# macOS: brew install trivy
# Linux: See https://aquasecurity.github.io/trivy/latest/getting-started/installation/

# Scan filesystem
trivy fs --severity CRITICAL,HIGH,MEDIUM .

# Scan Docker image
trivy image semiprime-api:test
```

## Troubleshooting

### CI Failures

**Frontend build fails:**
- Check `package-lock.json` is committed
- Verify Node.js version compatibility
- Run `npm ci` locally to test

**API tests fail:**
- Ensure PostgreSQL/Redis services start correctly
- Check database credentials in workflow
- Verify system dependencies (GMP, MPFR, MPC)

**Docker build fails:**
- Check Dockerfile syntax
- Verify build context paths
- Test locally with same build args

### Deployment Issues

**SSH connection fails:**
- Verify `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_KEY` secrets
- Check firewall rules on production server
- Test SSH connection manually: `ssh -i key user@host`

**Health check fails:**
- Services may need more startup time
- Check container logs: `docker compose logs`
- Verify health check endpoints work

**Rollback needed:**
- Workflow automatically rolls back on failure
- Manual rollback: `git checkout previous_tag && docker compose up -d`

## Maintenance

### Update Dependencies

**Python:**
```bash
cd api
pip install --upgrade pip
pip list --outdated
pip install --upgrade package_name
pip freeze > requirements.txt
```

**Node.js:**
```bash
cd frontend
npm outdated
npm update
npm audit fix
```

### Rotate Secrets

```bash
# Generate new SSH key
ssh-keygen -t ed25519 -C "github-actions@semiprime"

# Update DEPLOY_KEY secret in GitHub
# Copy public key to server: ~/.ssh/authorized_keys
```

### Monitor Workflow Usage

```
Settings → Actions → General → Usage this month
```

## Best Practices

1. **Always run CI locally first** before pushing
2. **Use feature branches** and create PRs
3. **Require reviews** for production deployments
4. **Monitor security alerts** and fix promptly
5. **Keep dependencies updated** weekly
6. **Test rollback procedures** regularly
7. **Use semantic versioning** for releases (v1.2.3)
8. **Document breaking changes** in release notes

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Buildx](https://docs.docker.com/buildx/working-with-buildx/)
- [Trivy Security Scanner](https://aquasecurity.github.io/trivy/)
- [CodeQL](https://codeql.github.com/)
- [Act - Local Actions Runner](https://github.com/nektos/act)
