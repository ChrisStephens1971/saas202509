#!/bin/bash

#################################
# HOA Accounting System - Staging Deployment Script
# Automates the full staging deployment process
#################################

set -e  # Exit on any error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="HOA Accounting System"
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env.production"

# Helper functions
function print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

function print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

function print_error() {
    echo -e "${RED}❌ $1${NC}"
}

function print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Main deployment script
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   $PROJECT_NAME - Staging Deploy   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

#################################
# 1. Pre-deployment Checks
#################################
print_header "1. PRE-DEPLOYMENT CHECKS"

# Check Docker
print_info "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_success "Docker installed: $(docker --version)"

# Check Docker Compose
print_info "Checking Docker Compose installation..."
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
print_success "Docker Compose installed: $(docker-compose --version)"

# Check .env.production
print_info "Checking environment configuration..."
if [ ! -f .env.production ]; then
    print_error ".env.production file not found!"
    print_info "Creating from template..."
    if [ -f .env.production.example ]; then
        cp .env.production.example .env.production
        print_warning "Created .env.production from template. Please edit it with your values!"
        print_info "Edit .env.production and run this script again."
        exit 1
    else
        print_error ".env.production.example not found. Cannot proceed."
        exit 1
    fi
fi
print_success "Environment file exists"

# Check for running containers
print_info "Checking for existing containers..."
RUNNING=$(docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE ps -q 2>/dev/null | wc -l)
if [ "$RUNNING" -gt 0 ]; then
    print_warning "Found $RUNNING running containers. They will be stopped and rebuilt."
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Deployment cancelled."
        exit 0
    fi
fi

#################################
# 2. Stop Existing Services
#################################
print_header "2. STOPPING EXISTING SERVICES"

print_info "Stopping containers..."
docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE down 2>/dev/null || true
print_success "Services stopped"

#################################
# 3. Build Docker Images
#################################
print_header "3. BUILDING DOCKER IMAGES"

print_info "Building images (this may take a few minutes)..."
docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE build --no-cache

print_success "Images built successfully"

#################################
# 4. Start Services
#################################
print_header "4. STARTING SERVICES"

print_info "Starting containers in background..."
docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d

# Wait for services to be healthy
print_info "Waiting for services to be ready..."
sleep 10

# Check service status
print_info "Checking service status..."
docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE ps

HEALTHY=$(docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE ps | grep -c "Up" || echo "0")
if [ "$HEALTHY" -lt 3 ]; then
    print_error "Some services failed to start. Check logs with: docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE logs"
    exit 1
fi
print_success "All services are running"

#################################
# 5. Database Setup
#################################
print_header "5. DATABASE SETUP"

# Wait for database to be ready
print_info "Waiting for database to be ready..."
for i in {1..30}; do
    if docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE exec -T backend python manage.py check --database default &>/dev/null; then
        break
    fi
    echo -n "."
    sleep 2
done
echo ""
print_success "Database is ready"

# Run migrations
print_info "Running database migrations..."
docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE exec -T backend python manage.py migrate
print_success "Migrations complete"

# Check if superuser exists
print_info "Checking for superuser..."
SUPERUSER_EXISTS=$(docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE exec -T backend python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
print(User.objects.filter(is_superuser=True).exists())
EOF
)

if [[ "$SUPERUSER_EXISTS" == *"False"* ]]; then
    print_warning "No superuser found. You'll need to create one."
    print_info "Run: docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE exec backend python manage.py createsuperuser"
else
    print_success "Superuser exists"
fi

#################################
# 6. Static Files
#################################
print_header "6. STATIC FILES"

print_info "Collecting static files..."
docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE exec -T backend python manage.py collectstatic --no-input
print_success "Static files collected"

#################################
# 7. Create Test Tenant
#################################
print_header "7. TEST DATA SETUP"

print_info "Checking for test tenant..."
TEST_TENANT_EXISTS=$(docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE exec -T backend python manage.py shell <<EOF
from tenants.models import Tenant
print(Tenant.objects.filter(slug='test-hoa').exists())
EOF
)

if [[ "$TEST_TENANT_EXISTS" == *"False"* ]]; then
    print_info "Creating test tenant..."
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE exec -T backend python manage.py shell <<EOF
from tenants.models import Tenant
tenant = Tenant.objects.create(
    name="Test HOA",
    slug="test-hoa",
    is_active=True
)
print(f"Created tenant: {tenant.name} ({tenant.id})")
EOF
    print_success "Test tenant created"
else
    print_success "Test tenant already exists"
fi

#################################
# 8. Verification
#################################
print_header "8. DEPLOYMENT VERIFICATION"

# Test frontend
print_info "Testing frontend..."
if curl -s -f http://localhost > /dev/null 2>&1; then
    print_success "Frontend is accessible at http://localhost"
else
    print_error "Frontend is not accessible"
fi

# Test backend API
print_info "Testing backend API..."
if curl -s -f http://localhost/api/v1/ > /dev/null 2>&1; then
    print_success "Backend API is accessible at http://localhost/api/v1/"
else
    print_error "Backend API is not accessible"
fi

# Test admin
print_info "Testing admin panel..."
if curl -s -f http://localhost/admin/ > /dev/null 2>&1; then
    print_success "Admin panel is accessible at http://localhost/admin/"
else
    print_error "Admin panel is not accessible"
fi

#################################
# 9. Display Info
#################################
print_header "9. DEPLOYMENT COMPLETE!"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Staging Deployment Successful! 🎉       ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
echo ""

echo "Access Points:"
echo "  Frontend:  http://localhost"
echo "  API:       http://localhost/api/v1/"
echo "  Admin:     http://localhost/admin/"
echo ""

echo "Useful Commands:"
echo "  View logs:        docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE logs -f"
echo "  Stop services:    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE stop"
echo "  Restart services: docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE restart"
echo "  Shell access:     docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE exec backend python manage.py shell"
echo "  Run tests:        ./smoke_tests.sh"
echo ""

echo "Next Steps:"
echo "  1. Create superuser if needed:  docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE exec backend python manage.py createsuperuser"
echo "  2. Run smoke tests:             ./smoke_tests.sh"
echo "  3. Test features manually"
echo "  4. Run performance tests:       locust -f locustfile.py"
echo "  5. Run security audit:          ./security-audit.sh"
echo ""

print_success "Deployment complete!"
