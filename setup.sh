#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check if UV is installed
check_uv() {
    print_info "Checking for UV package manager..."
    if ! command -v uv &> /dev/null; then
        print_error "UV is not installed"
        echo "Please install UV from https://docs.astral.sh/uv/getting-started/installation/"
        echo "Or run: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    print_success "UV is installed"
}

# Check if Docker and Docker Compose are installed
check_docker() {
    print_info "Checking for Docker and Docker Compose..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo "Please install Docker from https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker is installed"

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
        exit 1
    fi
    print_success "Docker Compose is installed"
}

# Install Python dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."
    uv sync
    print_success "Dependencies installed"
}

# Create .env file if it doesn't exist
setup_env() {
    print_info "Setting up environment variables..."
    if [ -f .env ]; then
        print_success ".env file already exists"
    else
        if [ ! -f .env.example ]; then
            print_error ".env.example file not found"
            exit 1
        fi
        cp .env.example .env
        print_success ".env file created from .env.example"
        echo ""
        echo -e "${YELLOW}IMPORTANT: Edit .env and add your GOOGLE_API_KEY${NC}"
        echo "Your current .env file:"
        cat .env
        echo ""
    fi
}

# Start PostgreSQL
start_postgres() {
    print_info "Starting PostgreSQL with Docker Compose..."
    docker-compose up -d
    
    print_info "Waiting for PostgreSQL to be ready..."
    sleep 5
    
    max_attempts=30
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if docker-compose exec -T postgres pg_isready -U rewindAI_admin &> /dev/null; then
            print_success "PostgreSQL is ready"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts: Waiting for PostgreSQL..."
        sleep 2
        ((attempt++))
    done
    
    print_error "PostgreSQL failed to start within timeout"
    exit 1
}

# Initialize database
init_database() {
    print_info "Initializing database..."
    uv run scripts/postgres_init.py
    print_success "Database initialized"
    
    print_info "Initializing LangGraph tables..."
    uv run scripts/postgres_init_langgraph.py
    print_success "LangGraph tables initialized"
}

# Main setup flow
main() {
    echo ""
    echo "======================================"
    echo "RewindAI Setup Script"
    echo "======================================"
    echo ""

    check_uv
    echo ""
    
    check_docker
    echo ""
    
    install_dependencies
    echo ""
    
    setup_env
    echo ""
    
    read -p "Start PostgreSQL now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        start_postgres
        echo ""
        
        init_database
        echo ""
    else
        print_info "Skipping PostgreSQL setup"
        echo "To start PostgreSQL later, run: docker-compose up -d"
        echo "Then run database initialization: uv run scripts/postgres_init.py && uv run scripts/postgres_init_langgraph.py"
        echo ""
    fi

    echo ""
    echo "======================================"
    print_success "Setup completed successfully!"
    echo "======================================"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env and add your GOOGLE_API_KEY"
    echo "2. Run the application: uv run -m app.main"
    echo ""
}

main
