#!/bin/bash

# AudioChimp API Startup Script
# This script helps you start the AudioChimp API either with Docker or locally

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Docker
check_docker() {
    if command_exists docker && command_exists docker-compose; then
        return 0
    else
        return 1
    fi
}

# Function to start with Docker
start_docker() {
    print_status "Starting AudioChimp API with Docker..."

    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found. Are you in the right directory?"
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Created .env file from .env.example"
        else
            print_warning "No .env.example found. Using default configuration."
            touch .env
        fi
    fi

    print_status "Building and starting containers..."
    docker-compose up --build -d

    print_success "AudioChimp API is starting up!"
    print_status "API will be available at: http://localhost:8000"
    print_status "API documentation: http://localhost:8000/docs"
    print_status "Health check: http://localhost:8000/health"

    print_status "Checking container status..."
    sleep 5
    docker-compose ps

    print_status "To view logs: docker-compose logs -f"
    print_status "To stop: docker-compose down"
}

# Function to start locally
start_local() {
    print_status "Starting AudioChimp API locally..."

    # Check Python
    if ! command_exists python; then
        print_error "Python is not installed. Please install Python 3.9+"
        exit 1
    fi

    # Check if we're in a virtual environment
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        print_status "Using virtual environment: $VIRTUAL_ENV"
    else
        print_warning "Not in a virtual environment. Consider using one."
    fi

    # Install dependencies if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        print_status "Installing dependencies..."
        pip install -r requirements.txt
    fi

    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Created .env file from .env.example"
        else
            print_warning "No .env.example found. Using default configuration."
            touch .env
        fi
    fi

    print_status "Starting AudioChimp API..."
    python -m auditchimp.main
}

# Function to show help
show_help() {
    echo "AudioChimp API Startup Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  docker    Start with Docker (recommended)"
    echo "  local     Start locally with Python"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 docker    # Start with Docker Compose"
    echo "  $0 local     # Start locally"
    echo ""
    echo "For more information, see README.md"
}

# Main script logic
case "${1:-help}" in
    "docker")
        if check_docker; then
            start_docker
        else
            print_error "Docker and/or Docker Compose not found."
            print_status "Please install Docker and Docker Compose to use this option."
            print_status "Alternatively, run '$0 local' to start locally."
            exit 1
        fi
        ;;
    "local")
        start_local
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Invalid option: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
