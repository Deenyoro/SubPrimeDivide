<div align="center">
  <img src="./horizontallogo.svg" alt="SemiPrimeDivide" width="600" />

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
  <img src="./logo.svg" alt="SemiPrimeDivide Logo" width="120" />
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
# Docker & Docker Compose
sudo apt-get update
sudo apt-get install docker.io docker-compose-plugin

# Enable buildx for multi-arch (optional)
docker buildx create --use
```

### macOS (Apple Silicon)
```bash
# Install Docker Desktop for Mac (includes Compose)
# https://www.docker.com/products/docker-desktop/

# Ensure Docker Desktop is running
docker ps
```

## Quick Start

### 1. Clone and Setup

```bash
cd /opt/docker/SemiPrimeDivide

# Copy environment template
cp .env.example .env

# (Optional) Edit .env for custom configuration
nano .env
```

### 2. Start Services

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Check health
docker compose ps
```

### 3. Access the Application

- **Web UI**: http://localhost:3000
- **API Docs**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/api/health

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

## Multi-Arch Builds (amd64 + arm64)

To build and push multi-platform images:

```bash
# Enable buildx
docker buildx create --use

# Build and push API
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t yourorg/factor-api:latest \
  --push -f infra/dockerfiles/Dockerfile.api api/

# Build and push worker
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t yourorg/factor-worker:latest \
  --push -f infra/dockerfiles/Dockerfile.worker api/

# Build and push frontend
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t yourorg/factor-frontend:latest \
  --push -f infra/dockerfiles/Dockerfile.frontend frontend/
```

Update `docker-compose.yml` to use your images:

```yaml
services:
  api:
    image: yourorg/factor-api:latest
  worker:
    image: yourorg/factor-worker:latest
  frontend:
    image: yourorg/factor-frontend:latest
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
# Check logs
docker compose logs api
docker compose logs worker

# Restart services
docker compose restart

# Rebuild if code changed
docker compose up -d --build
```

### Database connection errors

```bash
# Check DB is healthy
docker compose ps db

# Recreate DB
docker compose down -v
docker compose up -d db
```

### Worker not picking up jobs

```bash
# Check Redis
docker compose ps queue

# Check worker logs
docker compose logs worker

# Restart worker
docker compose restart worker
```

### Frontend can't connect to API

Check `NEXT_PUBLIC_API_URL` in frontend environment matches your API host.

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

## Contributing

Contributions welcome! Areas for improvement:

- GNFS integration (Cado-NFS)
- Additional equation methods
- Primality certificates (ECPP)
- Distributed workers (across machines)
- GPU acceleration (CUDA-ECM)

## License

MIT License - see LICENSE file

## References

- [Miller-Rabin Primality Test](https://en.wikipedia.org/wiki/Miller%E2%80%93Rabin_primality_test)
- [Pollard's Rho Algorithm](https://en.wikipedia.org/wiki/Pollard%27s_rho_algorithm)
- [Lenstra Elliptic Curve Factorization](https://en.wikipedia.org/wiki/Lenstra_elliptic-curve_factorization)
- [General Number Field Sieve](https://en.wikipedia.org/wiki/General_number_field_sieve)
- [GMP-ECM](https://www.loria.fr/~zimmerma/software/ecm/)
- [RSA Factoring Challenge](https://en.wikipedia.org/wiki/RSA_Factoring_Challenge)

## Support

For issues or questions, please open an issue on GitHub or contact the maintainers.

---

<div align="center">
  <img src="./logo.svg" alt="SemiPrimeDivide" width="80" />

  <p><strong>Built with</strong></p>
  <p>Python • FastAPI • Celery • PostgreSQL • Redis • Next.js • React • TailwindCSS • Docker</p>
</div>
