#!/bin/bash

echo "=========================================="
echo "  SemiPrime Factor - Quick Start"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "ERROR: Docker Compose is not available. Please install Docker Compose plugin."
    exit 1
fi

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env created"
fi

echo ""
echo "Starting services..."
echo ""

# Start services
docker compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 5

# Check health
echo ""
echo "Checking service health..."
docker compose ps

echo ""
echo "=========================================="
echo "  Services are starting!"
echo "=========================================="
echo ""
echo "  Web UI:       http://localhost:3000"
echo "  API Docs:     http://localhost:8080/docs"
echo "  Health Check: http://localhost:8080/api/health"
echo ""
echo "To view logs:   docker compose logs -f"
echo "To stop:        docker compose down"
echo ""
echo "Sample CSV:     data/samples/example_numbers.csv"
echo ""
