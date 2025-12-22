#!/bin/bash

# ============================================================================
# Cloud Computing AI SaaS - Complete Automated Setup Script
# ============================================================================
# This script fully automates the installation on a fresh Linux VM.
# It handles: Git, Docker, SSL, cloning repo, and starting services.
#
# Requirements: Fresh Linux VM with internet connection
# Usage: 
#   1. Download this script to your VM
#   2. chmod +x setup.sh
#   3. ./setup.sh
# ============================================================================

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration - MODIFY THESE BEFORE RUNNING
REPO_URL="https://github.com/5CCSACCA/coursework-Armitaeslami.git"  # Your repo URL
REPO_BRANCH="main"  # Default branch
PROJECT_DIR="coursework-Armitaeslami"  # Directory name for cloned repo

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

print_success() {
    echo -e "${CYAN}[SUCCESS]${NC} $1"
}

# Function to print a separator
print_separator() {
    echo "=============================================================================="
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
    if [ "$TOTAL_MEM" -lt 7 ]; then
        print_warning "System has ${TOTAL_MEM}GB RAM. BitNet LLM requires at least 8GB."
        print_warning "The system may run slowly or the LLM service may fail."
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_info "System has ${TOTAL_MEM}GB RAM - OK"
    fi
    
    # Check available disk space (need at least 15GB)
    AVAILABLE_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$AVAILABLE_SPACE" -lt 15 ]; then
        print_error "Insufficient disk space. Need at least 15GB free, have ${AVAILABLE_SPACE}GB."
        print_error "The project requires ~10GB for Docker images (LLM model is 4GB)"
        exit 1
    else
        print_info "Available disk space: ${AVAILABLE_SPACE}GB - OK"
    fi
}

# Function to install Git
install_git() {
    print_step "Installing Git..."
    
    if command_exists git; then
        print_info "Git is already installed: $(git --version)"
        return 0
    fi
    
    case $DISTRO in
        ubuntu|debian)
            sudo apt-get update
            sudo apt-get install -y git
            ;;
        fedora|rhel|centos)
            sudo dnf install -y git
            ;;
        arch|manjaro)
            sudo pacman -Sy --noconfirm git
            ;;
        *)
            print_error "Unsupported distribution for automatic Git installation"
            print_info "Please install Git manually: sudo apt-get install git"
            exit 1
            ;;
    esac
    
    if command_exists git; then
        print_success "Git installed successfully: $(git --version)"
    else
        print_error "Git installation failed"
        exit 1
    fi
}

# Function to get repository URL from user
get_repo_url() {
    if [ -z "$REPO_URL" ]; then
        echo ""
        print_step "Repository Setup"
        echo ""
        echo "Please provide your Git repository URL."
        echo "Examples:"
        echo "  HTTPS: https://github.com/username/repository.git"
        echo "  SSH:   git@github.com:username/repository.git"
        echo ""
        read -p "Enter repository URL: " REPO_URL
        
        if [ -z "$REPO_URL" ]; then
            print_error "Repository URL cannot be empty"
            exit 1
        fi
        
        echo ""
        read -p "Enter branch name (default: main): " BRANCH_INPUT
        if [ -n "$BRANCH_INPUT" ]; then
            REPO_BRANCH="$BRANCH_INPUT"
        fi
    fi
    
    print_info "Repository: $REPO_URL"
    print_info "Branch: $REPO_BRANCH"
}

# Function to clone repository
clone_repository() {
    print_step "Cloning repository..."
    
    # Check if directory already exists
    if [ -d "$PROJECT_DIR" ]; then
        print_warning "Directory '$PROJECT_DIR' already exists"
        read -p "Remove and re-clone? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_DIR"
        else
            print_info "Using existing directory"
            cd "$PROJECT_DIR"
            return 0
        fi
    fi
    
    # Clone the repository
    print_info "Cloning from $REPO_URL..."
    if git clone -b "https://github.com/5CCSACCA/coursework-Armitaeslami/tree/main"; then
        print_success "Repository cloned successfully"
        cd "$PROJECT_DIR"
    else
        print_error "Failed to clone repository"
        print_error "Please check:"
        print_error "  1. Repository URL is correct"
        print_error "  2. You have access to the repository"
        print_error "  3. Branch name is correct"
        print_error "  4. Your SSH key is set up (if using SSH)"
        exit 1
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
    
    print_success "Docker installed successfully"
}

# Function to add user to docker group
setup_docker_permissions() {
    print_step "Setting up Docker permissions..."
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    print_info "Added $USER to docker group"
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

# Function to check for required project files
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
        print_error "Missing required project files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        print_error "Make sure you're in the correct directory and all files are committed to git"
        exit 1
    fi
    
    print_success "All required project files found"
}

# Function to setup Firebase credentials
setup_firebase_credentials() {
    print_step "Setting up Firebase credentials..."
    
    # Create directory if it doesn't exist
    mkdir -p api-gateway/app
    
    if [ -f "api-gateway/app/firebase_key.json" ]; then
        print_success "firebase_key.json already exists"
        return 0
    fi
    
    echo ""
    print_warning "Firebase credentials not found!"
    echo ""
    echo "You need to add your Firebase service account key."
    echo "Options:"
    echo ""
    echo "  1. Paste JSON content now (recommended for first-time setup)"
    echo "  2. Upload file later via SCP/SFTP"
    echo "  3. Skip for now (services will fail without it)"
    echo ""
    read -p "Choose option (1/2/3): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            echo ""
            print_info "Please paste your Firebase JSON content below."
            print_info "Press Ctrl+D when done:"
            echo ""
            cat > api-gateway/app/firebase_key.json
            
            if [ -s "api-gateway/app/firebase_key.json" ]; then
                print_success "Firebase credentials saved"
            else
                print_warning "No content was pasted. You'll need to add it manually."
            fi
            ;;
        2)
            echo ""
            print_info "Upload firebase_key.json to: $(pwd)/api-gateway/app/"
            print_info "Example: scp firebase_key.json user@vm:$(pwd)/api-gateway/app/"
            read -p "Press Enter when done uploading..."
            
            if [ -f "api-gateway/app/firebase_key.json" ]; then
                print_success "Firebase credentials found"
            else
                print_warning "File not found. Continuing without Firebase credentials."
            fi
            ;;
        3)
            print_warning "Skipping Firebase setup. You'll need to add it manually later."
            ;;
        *)
            print_warning "Invalid option. Skipping Firebase setup."
            ;;
    esac
}

# Function to generate SSL certificates
generate_ssl_certificates() {
    print_step "Generating SSL certificates for HTTPS..."
    
    if [ -f "api-gateway/cert.pem" ] && [ -f "api-gateway/key.pem" ]; then
        print_info "SSL certificates already exist"
        return 0
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
        print_success "SSL certificates generated successfully"
        print_info "  Certificate: api-gateway/cert.pem"
        print_info "  Private Key: api-gateway/key.pem"
    else
        print_error "Failed to generate SSL certificates"
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
        print_info "prometheus.yml already exists, skipping"
        return 0
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
    
    print_success "Prometheus configuration created"
}

# Function to setup Grafana directories
setup_grafana_directories() {
    print_step "Setting up Grafana directories..."
    
    mkdir -p grafana/provisioning/datasources
    mkdir -p grafana/provisioning/dashboards
    
    print_success "Grafana directories created"
}

# Function to build Docker images
build_docker_images() {
    print_step "Building Docker images..."
    
    echo ""
    print_warning "This will take 10-20 minutes and download ~10GB"
    print_warning "The LLM service alone downloads a 4GB model"
    echo ""
    read -p "Start building now? (y/n) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Skipping build. Run 'docker compose build' manually later."
        return 0
    fi
    
    print_info "Building all services..."
    print_info "Progress will be shown below. Please be patient..."
    echo ""
    
    # Build with sg docker for immediate group access
    if sg docker -c "docker compose build"; then
        print_success "Docker images built successfully"
        return 0
    elif docker compose build; then
        print_success "Docker images built successfully"
        return 0
    else
        print_error "Build failed"
        print_info "You can retry later with: docker compose build"
        return 1
    fi
}

# Function to start services
start_services() {
    print_step "Starting all services..."
    
    echo ""
    read -p "Start services now? (y/n) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Skipping service start. Run 'docker compose up -d' manually later."
        return 0
    fi
    
    print_info "Starting containers in detached mode..."
    
    if sg docker -c "docker compose up -d"; then
        print_success "Services started successfully"
    elif docker compose up -d; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        print_info "Try manually: docker compose up -d"
        return 1
    fi
    
    # Wait a bit for services to initialize
    print_info "Waiting for services to initialize..."
    sleep 5
    
    # Show status
    print_info "Container status:"
    sg docker -c "docker compose ps" 2>/dev/null || docker compose ps 2>/dev/null || true
}

# Function to run tests
run_tests() {
    print_step "Running basic health checks..."
    
    sleep 3  # Give services a moment
    
    echo ""
    print_info "Testing API Gateway..."
    if curl -k -s https://localhost:8000/health > /dev/null 2>&1; then
        print_success "✅ API Gateway is responding"
    else
        print_warning "⚠️  API Gateway not responding yet (may still be starting)"
    fi
    
    print_info "Testing Prometheus..."
    if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
        print_success "✅ Prometheus is healthy"
    else
        print_warning "⚠️  Prometheus not responding yet"
    fi
    
    echo ""
    print_info "Check detailed status with: docker compose ps"
    print_info "View logs with: docker compose logs -f"
}

# Function to display service URLs
display_service_urls() {
    echo ""
    print_separator
    print_step "Service URLs"
    print_separator
    echo ""
    echo "  📡 API Gateway (HTTPS):     ${GREEN}https://localhost:8000${NC}"
    echo "     Documentation:           ${GREEN}https://localhost:8000/docs${NC}"
    echo "     Health Check:            ${GREEN}curl -k https://localhost:8000/health${NC}"
    echo ""
    echo "  🤖 YOLO Service:            ${GREEN}http://localhost:8001${NC}"
    echo "  🧠 LLM Service:             ${GREEN}http://localhost:8002${NC}"
    echo ""
    echo "  🗄️  MongoDB:                 ${GREEN}mongodb://localhost:27017${NC}"
    echo ""
    echo "  📬 RabbitMQ Management:     ${GREEN}http://localhost:15672${NC}"
    echo "     Username: guest"
    echo "     Password: guest"
    echo ""
    echo "  📊 Prometheus:              ${GREEN}http://localhost:9090${NC}"
    echo "     Targets:                 ${GREEN}http://localhost:9090/targets${NC}"
    echo ""
    echo "  📈 Grafana:                 ${GREEN}http://localhost:3000${NC}"
    echo "     Username: admin"
    echo "     Password: admin"
    echo ""
}

# Function to display next steps
display_next_steps() {
    echo ""
    print_separator
    print_success "SETUP COMPLETE!"
    print_separator
    echo ""
    
    display_service_urls
    
    print_separator
    print_step "Useful Commands"
    print_separator
    echo ""
    echo "  View logs:              ${GREEN}docker compose logs -f${NC}"
    echo "  View specific service:  ${GREEN}docker compose logs -f api-gateway${NC}"
    echo "  Check status:           ${GREEN}docker compose ps${NC}"
    echo "  Restart services:       ${GREEN}docker compose restart${NC}"
    echo "  Stop services:          ${GREEN}docker compose down${NC}"
    echo "  Remove everything:      ${GREEN}docker compose down -v${NC}"
    echo ""
    
    print_separator
    print_step "Testing the API"
    print_separator
    echo ""
    echo "  1. Get a Firebase authentication token from your web app"
    echo "  2. Set it as a variable:"
    echo "     ${GREEN}TOKEN=\"your-firebase-id-token\"${NC}"
    echo ""
    echo "  3. Test object detection:"
    echo "     ${GREEN}curl -k -X POST https://localhost:8000/detect \\${NC}"
    echo "     ${GREEN}  -H \"Authorization: Bearer \$TOKEN\" \\${NC}"
    echo "     ${GREEN}  -F \"file=@test-image.jpg\"${NC}"
    echo ""
    
    print_separator
    print_step "Important Notes"
    print_separator
    echo ""
    echo "  ⚠️  SSL Certificate: Self-signed (browser will warn - this is normal)"
    echo "  ⚠️  Use ${GREEN}-k${NC} flag with curl for HTTPS (bypasses cert verification)"
    echo "  ⚠️  First run may take a few minutes for all services to fully start"
    echo "  ⚠️  LLM service uses 8GB RAM - monitor with: ${GREEN}docker stats${NC}"
    echo ""
    
    if [ ! -f "api-gateway/app/firebase_key.json" ]; then
        print_warning "Firebase credentials not configured!"
        print_warning "Add firebase_key.json to: api-gateway/app/firebase_key.json"
        print_warning "Then restart: docker compose restart api-gateway"
        echo ""
    fi
    
    print_separator
    print_info "Project directory: $(pwd)"
    print_info "For more information, see README.md"
    print_separator
    echo ""
}

# Function to display initial banner
display_banner() {
    clear
    echo ""
    print_separator
    echo "  ${CYAN}Cloud Computing AI SaaS - Complete Automated Setup${NC}"
    echo "  ${CYAN}YOLO Object Detection + BitNet LLM Story Generation${NC}"
    print_separator
    echo ""
    echo "  This script will:"
    echo "    1. Install Git (if needed)"
    echo "    2. Clone your repository"
    echo "    3. Install Docker & Docker Compose"
    echo "    4. Generate SSL certificates"
    echo "    5. Configure Prometheus & Grafana"
    echo "    6. Build Docker images (~10GB download)"
    echo "    7. Start all services"
    echo ""
    print_separator
    echo ""
}

# Main installation process
main() {
    # Display banner
    display_banner
    
    # Pre-flight checks
    check_root
    detect_distro
    check_system_requirements
    
    # Ask for confirmation
    read -p "Continue with full installation? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installation cancelled"
        exit 0
    fi
    
    echo ""
    print_separator
    print_step "Phase 1: Installing Dependencies"
    print_separator
    echo ""
    
    # Install Git
    install_git
    
    # Install Docker
    if command_exists docker; then
        print_info "Docker is already installed"
    else
        install_docker
        setup_docker_permissions
    fi
    
    verify_docker
    
    echo ""
    print_separator
    print_step "Phase 2: Repository Setup"
    print_separator
    echo ""
    
    # Get repository URL
    get_repo_url
    
    # Clone repository
    clone_repository
    
    # Check project files
    check_project_files
    
    echo ""
    print_separator
    print_step "Phase 3: Project Configuration"
    print_separator
    echo ""
    
    # Setup Firebase
    setup_firebase_credentials
    
    # Generate SSL certificates
    generate_ssl_certificates
    
    # Setup Prometheus & Grafana
    setup_prometheus_config
    setup_grafana_directories
    
    echo ""
    print_separator
    print_step "Phase 4: Building Docker Images"
    print_separator
    echo ""
    
    # Build images
    build_docker_images
    
    echo ""
    print_separator
    print_step "Phase 5: Starting Services"
    print_separator
    echo ""
    
    # Start services
    start_services
    
    # Run tests
    run_tests
    
    # Display completion message
    display_next_steps
}

# Trap errors
set -e
trap 'print_error "An error occurred at line $LINENO. Setup may be incomplete."; exit 1' ERR

# Run main function
main

exit 0