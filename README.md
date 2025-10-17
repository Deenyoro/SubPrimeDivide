<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./horizontallogo-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="./horizontallogo-light.svg">
    <img src="./horizontallogo-light.svg" alt="SemiPrimeDivide" width="600" />
  </picture>

  <p align="center">
    <strong>High-performance, equation-guided integer factorization service</strong>
  </p>

  <p align="center">
    Supporting multiple algorithms including Trial Division, Pollard-rho, ECM, and the custom Trurl equation-based method
  </p>
</div>

---

## Features

- **Equation-Guided Search**: Implements the Trurl semiprime equation method to narrow factor search ranges
- **Multiple Algorithms**: Trial division, Pollard-rho (Brent variant), Elliptic Curve Method (ECM)
- **Web Interface**: Modern React/Next.js UI with real-time progress tracking
- **Async Processing**: Celery workers handle long-running jobs with pause/resume/cancel support
- **WebSocket Streaming**: Live logs and progress updates
- **CSV Bulk Upload**: Process multiple numbers from CSV files
- **Multi-Platform**: Runs on both x86_64 (Ubuntu) and ARM64 (macOS M-chip) via Docker Compose

## Architecture

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./logo-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="./logo-light.svg">
    <img src="./logo-light.svg" alt="SemiPrimeDivide Logo" width="120" />
  </picture>
</div>

```
┌─────────────┐      ┌──────────────┐      ┌───────────────┐
│   Frontend  │─────▶│     API      │─────▶│    Worker     │
│  (Next.js)  │      │  (FastAPI)   │      │   (Celery)    │
└─────────────┘      └──────────────┘      └───────────────┘
                            │                       │
                            ▼                       ▼
                      ┌──────────┐          ┌──────────┐
                      │ Postgres │          │  Redis   │
                      └──────────┘          └──────────┘
```

### Services

- **frontend**: Next.js 14 + React + TailwindCSS
- **api**: FastAPI with WebSocket support
- **worker**: Celery workers running factorization algorithms
- **db**: PostgreSQL 16 for job/log/result storage
- **queue**: Redis 7 for Celery broker and result backend

## Prerequisites

### Ubuntu (x86_64)
```bash
# Install Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin

# Add user to docker group (logout/login required)
sudo usermod -aG docker $USER

# Verify installation
docker --version
docker compose version
```

### macOS (Intel & Apple Silicon)

**Option 1: Docker Desktop (Recommended)**
1. Download from https://www.docker.com/products/docker-desktop/
2. Install the .dmg package
3. Open Docker Desktop and wait for it to start
4. Verify in terminal:
```bash
docker --version
docker compose version
docker ps
```

**Option 2: Homebrew**
```bash
# Install Docker
brew install docker docker-compose

# Install and start colima (Docker runtime for macOS)
brew install colima
colima start --cpu 4 --memory 8 --disk 60

# Verify
docker ps
```

**For Apple Silicon (M1/M2/M3):**
- Docker Desktop automatically handles ARM64 images
- The pre-built images support `linux/arm64` natively
- No additional configuration needed

## Quick Start

### Option A: Using Pre-Built CI/CD Images (Fastest)

The project publishes multi-arch images to GitHub Container Registry on every commit.

```bash
# Clone repository
git clone https://github.com/Deenyoro/SubPrimeDivide.git
cd SubPrimeDivide

# Copy environment file
cp .env.example .env

# Pull and start using pre-built images
docker compose -f docker-compose.ghcr.yml up -d

# View logs
docker compose logs -f

# Check status
docker compose ps
```

**Available images:**
- `ghcr.io/deenyoro/semiprime-api:latest` (linux/amd64, linux/arm64)
- `ghcr.io/deenyoro/semiprime-worker:latest` (linux/amd64, linux/arm64)
- `ghcr.io/deenyoro/semiprime-frontend:latest` (linux/amd64, linux/arm64)

### Option B: Build Locally

```bash
# Clone repository
git clone https://github.com/Deenyoro/SubPrimeDivide.git
cd SubPrimeDivide

# Copy environment template
cp .env.example .env

# Build and start all services
docker compose up -d --build

# View logs
docker compose logs -f

# Check status
docker compose ps
```

### Access the Application

- **Web UI**: http://localhost:3000
- **API Docs**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/api/health

### First-Time Setup

```bash
# Wait for services to initialize (30-60 seconds)
docker compose logs -f api

# When you see "Application startup complete", you're ready
# Press Ctrl+C to exit logs

# Open browser to http://localhost:3000
```

## Usage

### Create a Job via Web UI

1. Navigate to http://localhost:3000
2. Click "New Factorization Job"
3. Enter your semiprime number (or click "Load RSA-260 Example")
4. Configure algorithm options
5. Click "Start Factorization"
6. Monitor progress in real-time

### Create a Job via API

```bash
curl -X POST http://localhost:8080/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "n": "143",
    "mode": "auto",
    "use_equation": true,
    "algorithm_policy": {
      "use_trial_division": true,
      "trial_division_limit": 10000000,
      "use_pollard_rho": true,
      "pollard_rho_iterations": 1000000,
      "use_ecm": true
    }
  }'
```

### Upload CSV

Create a CSV file with numbers to factor:

```csv
number,description
143,Test case 1
323,Test case 2
```

Upload via UI at http://localhost:3000/bulk-upload or via API:

```bash
curl -X POST http://localhost:8080/api/upload/csv \
  -F "file=@numbers.csv"
```

## The Trurl Equation Method

This implementation includes the custom equation-based factorization approach described in the original request:

Given a semiprime `pnp = p × q`:

1. **Equation**: `y = (((pnp^2/x) + x^2) / pnp)`
2. **Constraint**: When `y = 0`, we get bounds on the smaller factor `x`
3. **Property**: If `x` increases, `y` decreases (inverse relationship)
4. **Search**: Systematically test prime candidates in the bounded range

The solver computes initial bounds using:
- `lower_bound ≈ 10^(digits/3)`
- `upper_bound = √pnp`

Then uses primesieve to iterate only primes in that range, testing each for divisibility.

### Example: RSA-260

```python
# Input
pnp = 2211282552952966643528108525502623092761208950247001539441374831...

# Equation-derived bounds (approximate)
lower = 1.0 × 10^90
upper = 1.0 × 10^130

# Search only primes in [lower, upper]
# Test each prime p: if pnp % p == 0, found factor!
```

## Algorithms

### 1. Trial Division
- Fastest for small factors (< 10^7)
- Uses wheel factorization and primesieve
- Configurable limit

### 2. Pollard-Rho (Brent Variant)
- Probabilistic method
- Good for medium factors (up to ~30 digits)
- Very fast when it works

### 3. Elliptic Curve Method (ECM)
- Best for finding factors up to 40-50 digits
- Uses GMP-ECM (external C library)
- Configurable stages: (B1, curves)
  - Quick: (10000, 25)
  - Standard: (50000, 100)
  - Deep: (250000, 200)

### 4. Equation-Guided Prime Search
- Custom Trurl method
- Narrows search space using mathematical constraints
- Iterates only primes in computed range
- Efficient for semiprimes where factors are in known ranges

## Development

### Project Structure

```
SemiPrimeDivide/
├── api/                    # FastAPI backend
│   ├── app/
│   │   ├── algos/         # Factorization algorithms
│   │   ├── equations/     # Equation solver
│   │   ├── models/        # Database models
│   │   ├── routes/        # API endpoints
│   │   ├── services/      # Business logic
│   │   ├── main.py        # FastAPI app
│   │   └── worker.py      # Celery worker
│   └── requirements.txt
├── frontend/              # Next.js UI
│   ├── src/
│   │   ├── pages/        # Routes
│   │   ├── components/   # React components
│   │   └── styles/       # CSS
│   └── package.json
├── infra/
│   └── dockerfiles/      # Dockerfiles for each service
├── data/
│   └── samples/          # Example CSV files
├── docker-compose.yml
└── README.md
```

### Running Locally (Development Mode)

#### Backend

```bash
cd api

# Install dependencies
pip install -r requirements.txt

# Start Postgres & Redis
docker compose up -d db queue

# Run API
uvicorn app.main:app --reload --port 8080

# Run worker (separate terminal)
celery -A app.worker worker --loglevel=info
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

### Running Tests

```bash
# Backend tests
cd api
pytest

# Frontend tests
cd frontend
npm test
```

## Deployment

### Using Pre-Built Images

The project uses GitHub Actions CI/CD to automatically build and publish multi-arch Docker images:

**Available tags:**
- `latest` - Latest main branch build
- `master` - Latest master branch build
- `master-{commit}` - Specific commit builds
- `main-{commit}` - Specific commit builds

**Pull specific versions:**
```bash
# Latest stable
docker pull ghcr.io/deenyoro/semiprime-api:latest
docker pull ghcr.io/deenyoro/semiprime-worker:latest
docker pull ghcr.io/deenyoro/semiprime-frontend:latest

# Specific commit (example)
docker pull ghcr.io/deenyoro/semiprime-api:master-d1c1dce
```

**Deploy with specific versions:**

Edit `docker-compose.ghcr.yml`:
```yaml
services:
  api:
    image: ghcr.io/deenyoro/semiprime-api:master-d1c1dce
  worker:
    image: ghcr.io/deenyoro/semiprime-worker:master-d1c1dce
  frontend:
    image: ghcr.io/deenyoro/semiprime-frontend:master-d1c1dce
```

Then deploy:
```bash
docker compose -f docker-compose.ghcr.yml up -d
```

### Production Deployment

For production environments:

1. **Use specific version tags** (not `latest`)
2. **Set production environment variables**:
```bash
# Create production .env
cp .env.example .env.production

# Edit with production values
nano .env.production
```

3. **Run with production config**:
```bash
docker compose -f docker-compose.ghcr.yml --env-file .env.production up -d
```

4. **Enable SSL/TLS** (add reverse proxy):
```bash
# Example with nginx
docker run -d \
  --name nginx-proxy \
  -p 80:80 -p 443:443 \
  -v /etc/nginx/certs:/etc/nginx/certs:ro \
  -v /var/run/docker.sock:/tmp/docker.sock:ro \
  nginxproxy/nginx-proxy
```

### macOS Deployment Notes

**Apple Silicon (M1/M2/M3):**
- Use the `linux/arm64` images automatically
- Performance is excellent (native ARM64 execution)
- Docker Desktop handles everything transparently

**Intel Macs:**
- Use the `linux/amd64` images automatically
- Full compatibility with x86_64 images

**Verify architecture:**
```bash
docker image inspect ghcr.io/deenyoro/semiprime-api:latest | grep Architecture
```

### Scaling Workers

To handle more jobs concurrently:

```yaml
services:
  worker:
    image: ghcr.io/deenyoro/semiprime-worker:latest
    deploy:
      replicas: 4  # Run 4 worker instances
      resources:
        limits:
          cpus: '2'
          memory: 8G
```

Or scale manually:
```bash
docker compose -f docker-compose.ghcr.yml up -d --scale worker=4
```

## Configuration

### Environment Variables

See `.env.example` for all options. Key variables:

- `DATABASE_URL`: Postgres connection string
- `REDIS_URL`: Redis connection string
- `CELERY_BROKER_URL`: Celery broker (Redis)
- `CELERY_RESULT_BACKEND`: Celery results (Redis)
- `CORS_ORIGINS`: Allowed CORS origins (comma-separated)
- `NEXT_PUBLIC_API_URL`: API URL for frontend

### Algorithm Tuning

Edit job creation payload or UI form:

```json
{
  "algorithm_policy": {
    "use_trial_division": true,
    "trial_division_limit": 10000000,
    "use_pollard_rho": true,
    "pollard_rho_iterations": 1000000,
    "use_ecm": true
  },
  "ecm_params": {
    "stages": [
      [10000, 25],
      [50000, 100],
      [250000, 200]
    ]
  }
}
```

## Performance Notes

### Expectations

- **Small factors** (< 10^9): seconds (trial division)
- **Medium factors** (10-20 digits): minutes (Pollard-rho)
- **Large factors** (30-40 digits): hours to days (ECM)
- **Very large factors** (50+ digits): weeks to months (GNFS required)

### RSA-260

The RSA-260 example number is a **260-digit** (863-bit) semiprime that remains **unfactored** as of 2025. Factoring it would require:

1. Months to years of compute on a cluster
2. GNFS (General Number Field Sieve) implementation
3. Significant RAM and distributed coordination

This service provides the **foundation** and can manage such jobs, but GNFS integration (e.g., Cado-NFS) is optional and not included in the base setup.

## Troubleshooting

### Services won't start

```bash
# Check logs for all services
docker compose logs

# Check specific service
docker compose logs api
docker compose logs worker

# Restart all services
docker compose restart

# Full rebuild (if using local build)
docker compose down
docker compose up -d --build
```

### macOS-specific issues

**"Cannot connect to Docker daemon"**
```bash
# Ensure Docker Desktop is running
open -a Docker

# Or if using colima
colima start
```

**"Port already in use"**
```bash
# Find process using port
lsof -ti:3000  # or :8080, :5432, etc
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "3001:3000"  # Use different host port
```

**Slow performance on macOS**
- Allocate more resources in Docker Desktop (Preferences > Resources)
- Recommended: 4 CPUs, 8GB RAM, 60GB disk
- Use named volumes instead of bind mounts for better performance

### Database connection errors

```bash
# Check DB is running
docker compose ps db

# View DB logs
docker compose logs db

# Reset database (WARNING: deletes all data)
docker compose down -v
docker compose up -d db

# Wait for DB to be ready
docker compose logs -f db
# Look for "database system is ready to accept connections"
```

### Worker not picking up jobs

```bash
# Check Redis is running
docker compose ps queue

# Test Redis connection
docker compose exec queue redis-cli ping
# Should return: PONG

# Check worker logs
docker compose logs worker

# Check if worker is registered in Celery
docker compose exec worker celery -A app.worker inspect active

# Restart worker
docker compose restart worker
```

### Frontend can't connect to API

**Check environment variables:**
```bash
# Should match your API URL
docker compose exec frontend env | grep NEXT_PUBLIC_API_URL
```

**Test API directly:**
```bash
curl http://localhost:8080/api/health
# Should return: {"status":"healthy"}
```

**CORS issues in browser console:**
- Check `CORS_ORIGINS` in API environment includes your frontend URL
- Restart API after changing CORS settings

### Memory issues

**Worker crashes or jobs fail:**
```bash
# Check current memory limits
docker stats

# Increase worker memory in docker-compose.yml:
services:
  worker:
    deploy:
      resources:
        limits:
          memory: 16G  # Increase from 8G
```

### Permission denied errors on macOS

```bash
# Ensure Docker has access to the directory
# Go to: System Preferences > Privacy & Security > Files and Folders
# Enable Docker access

# Or move project to standard location
mv SemiPrimeDivide ~/Projects/
cd ~/Projects/SemiPrimeDivide
```

### Image pull failures

**Rate limit or network issues:**
```bash
# Use specific SHA digest for reliability
docker pull ghcr.io/deenyoro/semiprime-api@sha256:19a99288dd29...

# Or build locally instead
docker compose up -d --build
```

### Complete reset

If all else fails:
```bash
# Stop and remove everything
docker compose down -v --remove-orphans

# Remove all project images
docker rmi $(docker images 'ghcr.io/deenyoro/semiprime-*' -q)

# Clean Docker system
docker system prune -a --volumes

# Start fresh
docker compose -f docker-compose.ghcr.yml up -d
```

## API Reference

Full API docs available at http://localhost:8080/docs (Swagger UI).

### Key Endpoints

- `POST /api/jobs` - Create job
- `GET /api/jobs` - List jobs
- `GET /api/jobs/{id}` - Get job details
- `POST /api/jobs/{id}/control` - Pause/resume/cancel job
- `GET /api/jobs/{id}/logs` - Get job logs
- `GET /api/jobs/{id}/results` - Get factors
- `WS /api/jobs/{id}/stream` - Real-time log stream (WebSocket)
- `POST /api/upload/csv` - Upload CSV

## References

- [Miller-Rabin Primality Test](https://en.wikipedia.org/wiki/Miller%E2%80%93Rabin_primality_test)
- [Pollard's Rho Algorithm](https://en.wikipedia.org/wiki/Pollard%27s_rho_algorithm)
- [Lenstra Elliptic Curve Factorization](https://en.wikipedia.org/wiki/Lenstra_elliptic-curve_factorization)
- [General Number Field Sieve](https://en.wikipedia.org/wiki/General_number_field_sieve)
- [GMP-ECM](https://www.loria.fr/~zimmerma/software/ecm/)
- [RSA Factoring Challenge](https://en.wikipedia.org/wiki/RSA_Factoring_Challenge)

---

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./logo-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="./logo-light.svg">
    <img src="./logo-light.svg" alt="SemiPrimeDivide" width="80" />
  </picture>

  <p><strong>Built with</strong></p>
  <p>Python • FastAPI • Celery • PostgreSQL • Redis • Next.js • React • TailwindCSS • Docker</p>
</div>
