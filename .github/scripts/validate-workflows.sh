#!/bin/bash
# Workflow validation and local testing script

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}CI/CD Workflow Validation${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if we're in the right directory
if [ ! -d ".github/workflows" ]; then
    echo -e "${RED}Error: .github/workflows directory not found${NC}"
    echo "Please run this script from the repository root"
    exit 1
fi

# Count workflows
WORKFLOW_COUNT=$(ls -1 .github/workflows/*.yml 2>/dev/null | wc -l)
echo -e "${GREEN}✓${NC} Found $WORKFLOW_COUNT workflow files"

# Validate YAML syntax
echo ""
echo -e "${YELLOW}Validating YAML syntax...${NC}"

for file in .github/workflows/*.yml; do
    if command -v yamllint &> /dev/null; then
        if yamllint -d relaxed "$file" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} $(basename $file)"
        else
            echo -e "${RED}✗${NC} $(basename $file) - YAML syntax error"
            yamllint -d relaxed "$file"
        fi
    else
        # Basic YAML check with Python
        if python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $(basename $file)"
        else
            echo -e "${RED}✗${NC} $(basename $file) - YAML syntax error"
        fi
    fi
done

# Check for required secrets in workflows
echo ""
echo -e "${YELLOW}Checking for required secrets...${NC}"

REQUIRED_SECRETS=("DEPLOY_HOST" "DEPLOY_USER" "DEPLOY_KEY")
for secret in "${REQUIRED_SECRETS[@]}"; do
    if grep -r "$secret" .github/workflows/ > /dev/null; then
        echo -e "${YELLOW}!${NC} Workflow requires secret: $secret"
    fi
done

# Check Dockerfiles
echo ""
echo -e "${YELLOW}Validating Dockerfiles...${NC}"

for dockerfile in infra/dockerfiles/Dockerfile.*; do
    if [ -f "$dockerfile" ]; then
        if command -v hadolint &> /dev/null; then
            if hadolint "$dockerfile" > /dev/null 2>&1; then
                echo -e "${GREEN}✓${NC} $(basename $dockerfile)"
            else
                echo -e "${YELLOW}!${NC} $(basename $dockerfile) - has warnings"
                hadolint "$dockerfile" | head -5
            fi
        else
            echo -e "${GREEN}✓${NC} $(basename $dockerfile) - exists"
        fi
    fi
done

# Test Docker builds
echo ""
echo -e "${YELLOW}Testing Docker builds (this may take a while)...${NC}"

GIT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if command -v docker &> /dev/null; then
    # API
    if docker build -f infra/dockerfiles/Dockerfile.api \
        --build-arg GIT_COMMIT="$GIT_COMMIT" \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        -t semiprime-api:test ./api > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} API Docker build successful"
    else
        echo -e "${RED}✗${NC} API Docker build failed"
    fi

    # Frontend
    if docker build -f infra/dockerfiles/Dockerfile.frontend \
        --build-arg GIT_COMMIT="$GIT_COMMIT" \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        -t semiprime-frontend:test ./frontend > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Frontend Docker build successful"
    else
        echo -e "${RED}✗${NC} Frontend Docker build failed"
    fi

    # Worker
    if docker build -f infra/dockerfiles/Dockerfile.worker \
        --build-arg GIT_COMMIT="$GIT_COMMIT" \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        -t semiprime-worker:test ./api > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Worker Docker build successful"
    else
        echo -e "${RED}✗${NC} Worker Docker build failed"
    fi
else
    echo -e "${YELLOW}!${NC} Docker not found - skipping build tests"
fi

# Check for test files
echo ""
echo -e "${YELLOW}Checking test configuration...${NC}"

if [ -f "api/pytest.ini" ]; then
    echo -e "${GREEN}✓${NC} pytest.ini found"
else
    echo -e "${RED}✗${NC} pytest.ini not found"
fi

if [ -f "api/tests/conftest.py" ]; then
    echo -e "${GREEN}✓${NC} conftest.py found"
else
    echo -e "${RED}✗${NC} conftest.py not found"
fi

TEST_COUNT=$(find api/tests -name "test_*.py" 2>/dev/null | wc -l)
echo -e "${GREEN}✓${NC} Found $TEST_COUNT test files"

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Validation Complete${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Install act for local workflow testing: brew install act (macOS) or see https://github.com/nektos/act"
echo "2. Run workflows locally: act -j frontend-test"
echo "3. Configure GitHub secrets for deployment"
echo "4. Push to trigger CI/CD pipeline"
echo ""
echo -e "${YELLOW}Required GitHub Secrets:${NC}"
echo "  - DEPLOY_HOST (for deployment)"
echo "  - DEPLOY_USER (for deployment)"
echo "  - DEPLOY_KEY (for deployment)"
echo "  - DEPLOY_PORT (optional, default: 22)"
