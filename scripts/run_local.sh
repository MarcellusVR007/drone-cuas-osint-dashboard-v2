#!/bin/bash

# Script to run CUAS Dashboard V2 locally with Docker Compose

set -e

echo "=== CUAS Dashboard V2 - Local Setup ==="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
fi

echo "Step 1: Starting Docker Compose services..."
docker-compose up -d

echo ""
echo "Step 2: Waiting for PostgreSQL to be ready..."
sleep 5

echo ""
echo "Step 3: Running Alembic migrations..."
docker-compose exec backend alembic upgrade head

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Services running:"
echo "  - API:      http://localhost:8000"
echo "  - Docs:     http://localhost:8000/docs"
echo "  - ReDoc:    http://localhost:8000/redoc"
echo "  - Postgres: localhost:5432"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f backend"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""
