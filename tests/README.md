# Tests

This directory contains test scripts for the SemiPrime Factor project.

## Test Files

### `test_trurl_equation_simple.py`
Standalone test of Trurl's "find x when y=1" equation. No dependencies needed - pure Python for verification.

**Run:**
```bash
python3 tests/test_trurl_equation_simple.py
```

**Tests:**
- Finding x where y=1 using Newton's method
- Verification with known semiprimes (143, 1003001, etc.)
- Accuracy comparison with actual factors

### `test_trurl_y_equals_one.py`
Full integration test using the actual `SemiPrimeEquationSolver` class with gmpy2.

**Run:**
```bash
# In API container
docker compose exec api python /app/test_trurl_y_equals_one.py

# Or with dependencies installed locally
cd api && python ../tests/test_trurl_y_equals_one.py
```

**Tests:**
- Complete diagnostic reports
- RSA-100 and RSA-260 analysis
- Bound computation with y=1 method
- Comparison to heuristic bounds

### `test_trurl_method.py`
Original test script for the Trurl equation method.

**Run:**
```bash
cd api && python ../tests/test_trurl_method.py
```

## Running All Tests

### Backend Tests
```bash
cd api
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Docker-based Testing
```bash
# Start services
docker compose up -d

# Run API tests in container
docker compose exec api python -m pytest /app/tests/

# Run specific test
docker compose exec api python /app/../tests/test_trurl_equation_simple.py
```

## Test Organization

- **Unit tests**: Individual function/method tests
- **Integration tests**: Tests with database, API, etc.
- **Standalone tests**: Pure Python verification scripts (no deps)

## Adding New Tests

When adding tests:
1. Place in this `/tests` directory
2. Name with `test_` prefix for pytest discovery
3. Add entry to this README
4. Include docstring explaining what's tested
