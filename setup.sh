#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Function to install Docker
install_docker() {
    print_info "Installing Docker..."
    
    case $DISTRO in
        ubuntu|debian)
            # Update package index
            sudo apt-get update
            
            # Install prerequisites
            sudo apt-get install -y \
                ca-certificates \
                curl \
                gnupg \
                lsb-release
            
            # Add Docker's official GPG key
            sudo install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/$DISTRO/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            sudo chmod a+r /etc/apt/keyrings/docker.gpg
            
            # Set up the repository
            echo \
                "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$DISTRO \
                $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # Install Docker Engine
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            ;;
            
        fedora|rhel|centos)
            # Install prerequisites
            sudo dnf -y install dnf-plugins-core
            
            # Add Docker repository
            sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
            
            # Install Docker Engine
            sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            
            # Start Docker
            sudo systemctl start docker
            sudo systemctl enable docker
            ;;
            
        arch|manjaro)
            sudo pacman -Sy --noconfirm docker docker-compose
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
    print_info "Adding current user to docker group..."
    sudo usermod -aG docker $USER
    print_warning "You need to log out and log back in for group changes to take effect"
    print_warning "Or run: newgrp docker"
}

# Function to verify Docker installation
verify_docker() {
    print_info "Verifying Docker installation..."
    
    if docker --version >/dev/null 2>&1; then
        print_info "Docker version: $(docker --version)"
    else
        print_error "Docker installation verification failed"
        exit 1
    fi
    
    if docker compose version >/dev/null 2>&1; then
        print_info "Docker Compose version: $(docker compose version)"
    else
        print_error "Docker Compose installation verification failed"
        exit 1
    fi
}

# Function to check for required files
check_project_files() {
    print_info "Checking for required project files..."
    
    local required_files=(
        "docker-compose.yml"
        "api-gateway/Dockerfile"
        "yolo-service/Dockerfile"
        "llm-service/Dockerfile"
        "postprocessor-service/Dockerfile"
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

# Function to check for firebase_key.json
check_firebase_key() {
    if [ ! -f "firebase_key.json" ]; then
        print_warning "firebase_key.json not found!"
        print_warning "Please add your Firebase credentials file before starting the services"
        print_warning "Place it in the project root directory as 'firebase_key.json'"
    else
        print_info "firebase_key.json found"
    fi
}

# Function to create monitoring directories if they don't exist
setup_monitoring_directories() {
    print_info "Setting up monitoring directories..."
    
    mkdir -p monitoring/prometheus
    mkdir -p monitoring/grafana/provisioning/datasources
    mkdir -p monitoring/grafana/provisioning/dashboards
    
    # Create basic prometheus.yml if it doesn't exist
    if [ ! -f "monitoring/prometheus/prometheus.yml" ]; then
        print_warning "Creating basic prometheus.yml configuration..."
        cat > monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'api-gateway'
    static_configs:
      - targets: ['api-gateway:8000']

  - job_name: 'yolo-service'
    static_configs:
      - targets: ['yolo-service:8001']

  - job_name: 'llm-service'
    static_configs:
      - targets: ['llm-service:8002']
EOF
    fi
}

# Function to pull/build Docker images
setup_docker_images() {
    print_info "Pulling Docker images and building services..."
    
    # Try to use docker compose, otherwise it might fail on permissions
    if ! docker compose pull 2>/dev/null; then
        print_warning "Could not pull images. You may need to run 'newgrp docker' first or log out/in"
        print_info "Run 'docker compose pull' manually after fixing permissions"
    fi
}

# Function to display next steps
display_next_steps() {
    echo ""
    echo "=========================================="
    print_info "Setup completed successfully!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. If this is your first time, log out and log back in (or run 'newgrp docker')"
    echo ""
    echo "2. Ensure firebase_key.json is in the project root directory"
    echo ""
    echo "3. Start the services:"
    echo "   ${GREEN}docker compose up -d${NC}"
    echo ""
    echo "4. Check the status:"
    echo "   ${GREEN}docker compose ps${NC}"
    echo ""
    echo "5. View logs:"
    echo "   ${GREEN}docker compose logs -f${NC}"
    echo ""
    echo "6. Access the services:"
    echo "   - API Gateway:    http://localhost:8000"
    echo "   - YOLO Service:   http://localhost:8001"
    echo "   - LLM Service:    http://localhost:8002"
    echo "   - MongoDB:        mongodb://localhost:27017"
    echo "   - RabbitMQ:       http://localhost:15672 (user: guest, pass: guest)"
    echo "   - Prometheus:     http://localhost:9090"
    echo "   - Grafana:        http://localhost:3000 (user: admin, pass: admin)"
    echo ""
    echo "7. Stop the services:"
    echo "   ${GREEN}docker compose down${NC}"
    echo ""
    echo "8. Remove all data (careful!):"
    echo "   ${GREEN}docker compose down -v${NC}"
    echo ""
}

# Main installation process
main() {
    echo ""
    echo "=========================================="
    echo "  Docker & Project Setup Script"
    echo "=========================================="
    echo ""
    
    # Check if running as root
    check_root
    
    # Detect distribution
    detect_distro
    
    # Check if Docker is already installed
    if command_exists docker; then
        print_info "Docker is already installed"
        docker --version
    else
        install_docker
        setup_docker_permissions
    fi
    
    # Check if Docker Compose is available
    if docker compose version >/dev/null 2>&1; then
        print_info "Docker Compose is already available"
    else
        print_error "Docker Compose plugin not found"
        print_info "Please install it manually or reinstall Docker"
        exit 1
    fi
    
    # Verify installation
    verify_docker
    
    # Check project files
    check_project_files
    
    # Check for Firebase key
    check_firebase_key
    
    # Setup monitoring directories
    setup_monitoring_directories
    
    # Setup Docker images
    setup_docker_images
    
    # Display next steps
    display_next_steps
}

# Run main function
main