#!/bin/bash

# ============================================================================
# Cloud Computing AI SaaS - Automated Setup Script
# ============================================================================
# This script automates the installation and configuration of the entire
# project on a fresh Linux machine.
#
# Requirements: Linux machine with internet connection
# Usage: chmod +x setup.sh && ./setup.sh
# ============================================================================

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_error "Please do not run this script as root. It will request sudo when needed."
        exit 1
    fi
}

# Function to detect Linux distribution
detect_distro() {
    print_step "Detecting Linux distribution..."
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    else
        print_error "Cannot detect Linux distribution"
        exit 1
    fi
    print_info "Detected distribution: $DISTRO $VERSION"
}

# Function to check system requirements
check_system_requirements() {
    print_step "Checking system requirements..."
    
    # Check available memory (need at least 8GB for BitNet LLM)
    TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_MEM" -lt 8 ]; then
        print_warning "System has less than 8GB RAM. BitNet LLM requires at least 8GB."
        print_warning "The system may run slowly or fail. Consider upgrading RAM."
    else
        print_info "System has ${TOTAL_MEM}GB RAM - OK"
    fi
    
    # Check available disk space (need at least 10GB)
    AVAILABLE_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$AVAILABLE_SPACE" -lt 10 ]; then
        print_error "Insufficient disk space. Need at least 10GB free."
        exit 1
    else
        print_info "Available disk space: ${AVAILABLE_SPACE}GB - OK"
    fi
}

# Function to install Docker
install_docker() {
    print_step "Installing Docker..."
    
    case $DISTRO in
        ubuntu|debian)
            # Remove old Docker versions
            print_info "Removing old Docker versions if any..."
            sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
            
            # Update package index
            print_info "Updating package index..."
            sudo apt-get update
            
            # Install prerequisites
            print_info "Installing prerequisites..."
            sudo apt-get install -y \
                ca-certificates \
                curl \
                gnupg \
                lsb-release \
                openssl
            
            # Add Docker's official GPG key
            print_info "Adding Docker GPG key..."
            sudo install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/$DISTRO/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            sudo chmod a+r /etc/apt/keyrings/docker.gpg
            
            # Set up the repository
            print_info "Setting up Docker repository..."
            echo \
                "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$DISTRO \
                $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # Install Docker Engine
            print_info "Installing Docker Engine..."
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            ;;
            
        fedora|rhel|centos)
            # Remove old versions
            print_info "Removing old Docker versions if any..."
            sudo dnf remove -y docker \
                docker-client \
                docker-client-latest \
                docker-common \
                docker-latest \
                docker-latest-logrotate \
                docker-logrotate \
                docker-selinux \
                docker-engine-selinux \
                docker-engine 2>/dev/null || true
            
            # Install prerequisites
            print_info "Installing prerequisites..."
            sudo dnf -y install dnf-plugins-core openssl
            
            # Add Docker repository
            print_info "Adding Docker repository..."
            sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
            
            # Install Docker Engine
            print_info "Installing Docker Engine..."
            sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            
            # Start Docker
            print_info "Starting Docker service..."
            sudo systemctl start docker
            sudo systemctl enable docker
            ;;
            
        arch|manjaro)
            print_info "Installing Docker on Arch-based system..."
            sudo pacman -Sy --noconfirm docker docker-compose openssl
            sudo systemctl start docker
            sudo systemctl enable docker
            ;;
            
        *)
            print_error "Unsupported distribution: $DISTRO"
            print_info "Please install Docker manually from https://docs.docker.com/engine/install/"
            exit 1
            ;;
    esac
    
    print_info "Docker installed successfully"
}

# Function to add user to docker group
setup_docker_permissions() {
    print_step "Setting up Docker permissions..."
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    print_info "Added $USER to docker group"
    print_warning "Group changes will take effect after you log out and log back in"
    print_warning "For immediate effect in this session, run: newgrp docker"
}

# Function to verify Docker installation
verify_docker() {
    print_step "Verifying Docker installation..."
    
    # Try with newgrp to apply group changes immediately
    if sg docker -c "docker --version" >/dev/null 2>&1; then
        DOCKER_VERSION=$(sg docker -c "docker --version")
        print_info "Docker version: $DOCKER_VERSION"
    elif docker --version >/dev/null 2>&1; then
        print_info "Docker version: $(docker --version)"
    else
        print_error "Docker installation verification failed"
        print_error "Try logging out and back in, then run: docker --version"
        exit 1
    fi
    
    # Verify Docker Compose
    if sg docker -c "docker compose version" >/dev/null 2>&1; then
        COMPOSE_VERSION=$(sg docker -c "docker compose version")
        print_info "Docker Compose version: $COMPOSE_VERSION"
    elif docker compose version >/dev/null 2>&1; then
        print_info "Docker Compose version: $(docker compose version)"
    else
        print_error "Docker Compose installation verification failed"
        exit 1
    fi
}

# Function to check for required files
check_project_files() {
    print_step "Checking for required project files..."
    
    local required_files=(
        "docker-compose.yml"
        "api-gateway/Dockerfile"
        "api-gateway/requirements.txt"
        "yolo-service/Dockerfile"
        "yolo-service/requirements.txt"
        "llm-service/Dockerfile"
        "llm-service/requirements.txt"
        "postprocessor-service/Dockerfile"
        "postprocessor-service/requirements.txt"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -ne 0 ]; then
        print_error "Missing required files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        exit 1
    fi
    
    print_info "All required project files found"
}

# Function to check for Firebase credentials
check_firebase_key() {
    print_step "Checking for Firebase credentials..."
    
    if [ ! -f "api-gateway/app/firebase_key.json" ]; then
        print_error "firebase_key.json not found!"
        print_error "Please add your Firebase credentials before continuing:"
        print_error "  1. Download from Firebase Console"
        print_error "  2. Place at: api-gateway/app/firebase_key.json"
        
        read -p "Do you want to continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Setup cancelled. Please add firebase_key.json and run again."
            exit 1
        fi
        print_warning "Continuing without Firebase credentials - some features will fail!"
    else
        print_info "firebase_key.json found at api-gateway/app/firebase_key.json"
    fi
}

# Function to generate SSL certificates
generate_ssl_certificates() {
    print_step "Generating SSL certificates for HTTPS..."
    
    if [ -f "api-gateway/cert.pem" ] && [ -f "api-gateway/key.pem" ]; then
        print_info "SSL certificates already exist"
        read -p "Regenerate certificates? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi
    
    print_info "Generating self-signed SSL certificate (valid for 365 days)..."
    
    # Generate certificate using OpenSSL
    openssl req -x509 -newkey rsa:4096 -nodes \
        -out api-gateway/cert.pem \
        -keyout api-gateway/key.pem \
        -days 365 \
        -subj "/C=GB/ST=London/L=London/O=KCL/OU=CS/CN=localhost" \
        2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_info "SSL certificates generated successfully"
        print_info "  Certificate: api-gateway/cert.pem"
        print_info "  Private Key: api-gateway/key.pem"
    else
        print_error "Failed to generate SSL certificates"
        print_error "Please ensure OpenSSL is installed"
        exit 1
    fi
}

# Function to setup Prometheus configuration
setup_prometheus_config() {
    print_step "Setting up Prometheus configuration..."
    
    # Create prometheus directory if it doesn't exist
    mkdir -p prometheus
    
    # Create prometheus.yml with HTTPS support for API Gateway
    if [ -f "prometheus/prometheus.yml" ]; then
        print_info "prometheus.yml already exists"
        read -p "Overwrite prometheus.yml? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi
    
    print_info "Creating prometheus.yml with HTTPS configuration..."
    cat > prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'api-gateway'
    scheme: https
    tls_config:
      insecure_skip_verify: true
    static_configs:
      - targets: ['api-gateway:8000']

  - job_name: 'yolo-service'
    static_configs:
      - targets: ['yolo-service:8001']

  - job_name: 'llm-service'
    static_configs:
      - targets: ['llm-service:8002']
EOF
    
    print_info "Prometheus configuration created successfully"
}

# Function to setup Grafana directories
setup_grafana_directories() {
    print_step "Setting up Grafana directories..."
    
    mkdir -p grafana/provisioning/datasources
    mkdir -p grafana/provisioning/dashboards
    
    print_info "Grafana directories created"
}

# Function to create .gitignore if it doesn't exist
setup_gitignore() {
    print_step "Setting up .gitignore..."
    
    if [ ! -f ".gitignore" ]; then
        print_info "Creating .gitignore..."
        cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
env/
ENV/

# Docker
.dockerignore

# IDE
.vscode/
.idea/
*.swp
*.swo

# SSL Certificates (sensitive)
*.pem
cert.pem
key.pem

# Firebase credentials (sensitive)
firebase_key.json
*firebase_key.json

# MongoDB data
data/

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Test files
test.jpg
test.png
*.test.*
EOF
        print_info ".gitignore created"
    else
        print_info ".gitignore already exists"
    fi
}

# Function to pull Docker images
pull_docker_images() {
    print_step "Pulling required Docker images..."
    
    print_info "This may take several minutes depending on your internet speed..."
    
    # Try with newgrp first, fallback to regular docker command
    if sg docker -c "docker compose pull" 2>/dev/null; then
        print_info "Docker images pulled successfully"
    elif docker compose pull 2>/dev/null; then
        print_info "Docker images pulled successfully"
    else
        print_warning "Could not pull images automatically"
        print_warning "You may need to log out/in first, then run: docker compose pull"
        return 1
    fi
}

# Function to build Docker images
build_docker_images() {
    print_step "Building Docker images..."
    
    print_info "Building all services. This will take 10-20 minutes..."
    print_warning "The LLM service requires downloading a 4GB model - please be patient!"
    
    # Try with newgrp first, fallback to regular docker command
    if sg docker -c "docker compose build" 2>/dev/null; then
        print_info "Docker images built successfully"
    elif docker compose build 2>/dev/null; then
        print_info "Docker images built successfully"
    else
        print_error "Failed to build Docker images"
        print_error "You may need to log out/in first, then run: docker compose build"
        return 1
    fi
}

# Function to test Docker setup
test_docker_setup() {
    print_step "Testing Docker setup..."
    
    # Test running a simple container
    if sg docker -c "docker run --rm hello-world" >/dev/null 2>&1; then
        print_info "Docker is working correctly"
        return 0
    elif docker run --rm hello-world >/dev/null 2>&1; then
        print_info "Docker is working correctly"
        return 0
    else
        print_warning "Docker test failed - you may need to restart your session"
        return 1
    fi
}

# Function to display system information
display_system_info() {
    print_step "System Information Summary"
    echo ""
    echo "  Distribution:     $DISTRO $VERSION"
    echo "  Total Memory:     $(free -h | awk '/^Mem:/{print $2}')"
    echo "  Available Space:  $(df -h . | awk 'NR==2 {print $4}')"
    echo "  Docker Version:   $(docker --version 2>/dev/null || echo 'Not accessible yet')"
    echo "  Compose Version:  $(docker compose version 2>/dev/null || echo 'Not accessible yet')"
    echo ""
}

# Function to display next steps
display_next_steps() {
    echo ""
    echo "=============================================================================="
    print_info "Setup completed successfully!"
    echo "=============================================================================="
    echo ""
    
    print_step "IMPORTANT: Group Changes"
    echo ""
    echo "  Your user has been added to the 'docker' group."
    echo "  ${YELLOW}You MUST log out and log back in for this to take effect!${NC}"
    echo ""
    echo "  ${BLUE}After logging back in, continue with these steps:${NC}"
    echo ""
    
    print_step "1. Verify Docker Access"
    echo "     ${GREEN}docker --version${NC}"
    echo "     ${GREEN}docker compose version${NC}"
    echo ""
    
    print_step "2. Build the Project (if not done automatically)"
    echo "     ${GREEN}docker compose build${NC}"
    echo "     ${YELLOW}Note: This takes 10-20 minutes (downloads 4GB LLM model)${NC}"
    echo ""
    
    print_step "3. Start All Services"
    echo "     ${GREEN}docker compose up -d${NC}"
    echo ""
    
    print_step "4. Check Service Status"
    echo "     ${GREEN}docker compose ps${NC}"
    echo ""
    
    print_step "5. View Logs"
    echo "     ${GREEN}docker compose logs -f${NC}"
    echo "     ${GREEN}docker compose logs -f api-gateway${NC}  (specific service)"
    echo ""
    
    print_step "6. Access Services"
    echo ""
    echo "     📡 API Gateway (HTTPS): ${GREEN}https://localhost:8000${NC}"
    echo "        Documentation:       ${GREEN}https://localhost:8000/docs${NC}"
    echo "        Health Check:        ${GREEN}curl -k https://localhost:8000/health${NC}"
    echo ""
    echo "     🤖 YOLO Service:        ${GREEN}http://localhost:8001${NC}"
    echo "     🧠 LLM Service:         ${GREEN}http://localhost:8002${NC}"
    echo "     🗄️  MongoDB:             ${GREEN}mongodb://localhost:27017${NC}"
    echo "     📬 RabbitMQ Management: ${GREEN}http://localhost:15672${NC}"
    echo "        Username: guest"
    echo "        Password: guest"
    echo ""
    echo "     📊 Prometheus:          ${GREEN}http://localhost:9090${NC}"
    echo "        Targets:             ${GREEN}http://localhost:9090/targets${NC}"
    echo ""
    echo "     📈 Grafana:             ${GREEN}http://localhost:3000${NC}"
    echo "        Username: admin"
    echo "        Password: admin (will prompt to change)"
    echo ""
    
    print_step "7. Test the API"
    echo ""
    echo "     ${GREEN}# Get Firebase auth token first from your app${NC}"
    echo "     ${GREEN}TOKEN=\"your-firebase-id-token\"${NC}"
    echo ""
    echo "     ${GREEN}# Upload and detect objects${NC}"
    echo "     ${GREEN}curl -k -X POST https://localhost:8000/detect \\${NC}"
    echo "     ${GREEN}  -H \"Authorization: Bearer \$TOKEN\" \\${NC}"
    echo "     ${GREEN}  -F \"file=@test-image.jpg\"${NC}"
    echo ""
    
    print_step "8. Stop Services"
    echo "     ${GREEN}docker compose down${NC}"
    echo ""
    
    print_step "9. Remove All Data (careful!)"
    echo "     ${GREEN}docker compose down -v${NC}"
    echo ""
    
    print_step "Important Files Created"
    echo ""
    echo "     ✅ api-gateway/cert.pem       (SSL certificate)"
    echo "     ✅ api-gateway/key.pem        (SSL private key)"
    echo "     ✅ prometheus/prometheus.yml  (Prometheus config)"
    echo "     ⚠️  api-gateway/app/firebase_key.json (YOU must add this!)"
    echo ""
    
    print_step "Troubleshooting"
    echo ""
    echo "     If services fail to start:"
    echo "       1. Check logs:    ${GREEN}docker compose logs <service-name>${NC}"
    echo "       2. Rebuild:       ${GREEN}docker compose build <service-name>${NC}"
    echo "       3. Restart:       ${GREEN}docker compose restart <service-name>${NC}"
    echo ""
    echo "     If Docker commands fail:"
    echo "       1. ${YELLOW}Log out and log back in${NC}"
    echo "       2. Verify groups: ${GREEN}groups${NC} (should include 'docker')"
    echo "       3. Test Docker:   ${GREEN}docker run --rm hello-world${NC}"
    echo ""
    
    print_step "Documentation"
    echo ""
    echo "     📖 README.md - Complete project documentation"
    echo "     💰 pricing.md - Cost estimation"
    echo "     🔧 setup.sh - This setup script"
    echo ""
    
    echo "=============================================================================="
    print_info "For more information, see README.md"
    echo "=============================================================================="
    echo ""
}

# Main installation process
main() {
    echo ""
    echo "=============================================================================="
    echo "  Cloud Computing AI SaaS - Automated Setup"
    echo "  YOLO Object Detection + BitNet LLM Story Generation"
    echo "=============================================================================="
    echo ""
    
    # Pre-flight checks
    check_root
    detect_distro
    check_system_requirements
    
    # Display system info
    display_system_info
    
    # Ask for confirmation
    read -p "Continue with installation? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installation cancelled"
        exit 0
    fi
    
    # Docker installation
    if command_exists docker; then
        print_info "Docker is already installed"
        docker --version
    else
        install_docker
    fi
    
    # Setup permissions
    setup_docker_permissions
    
    # Verify Docker installation
    verify_docker
    
    # Test Docker
    test_docker_setup
    
    # Project-specific setup
    check_project_files
    check_firebase_key
    generate_ssl_certificates
    setup_prometheus_config
    setup_grafana_directories
    setup_gitignore
    
    # Pull and build images
    print_info "Would you like to pull and build Docker images now?"
    print_warning "This requires ~10GB download and takes 10-20 minutes"
    read -p "Pull and build now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pull_docker_images
        build_docker_images
    else
        print_info "Skipping image pull/build - you can do this later with:"
        print_info "  docker compose build"
    fi
    
    # Display next steps
    display_next_steps
}

# Trap errors
set -e
trap 'print_error "An error occurred. Setup may be incomplete."; exit 1' ERR

# Run main function
main

exit 0



### **Manual Tasks Remaining:**
#1. Add `firebase_key.json` (user must do this)
#2. Log out and log back in (for Docker group)
#3. Start services with `docker compose up -d`