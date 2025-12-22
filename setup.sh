#!/bin/bash

# ============================================================================
# Cloud Computing AI SaaS - Environment Setup Script
# ============================================================================
# This script sets up Docker and configures your already-cloned project.
#
# Prerequisites: Repository must be already cloned
# Usage: 
#   1. Clone your repository: git clone <your-repo>
#   2. cd into project directory
#   3. Run: chmod +x setup.sh && ./setup.sh
# ============================================================================

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_step() { echo -e "${BLUE}[STEP]${NC} $1"; }
print_success() { echo -e "${CYAN}[SUCCESS]${NC} $1"; }
print_separator() { echo "=============================================================================="; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_error "Don't run as root. Script will use sudo when needed."
        exit 1
    fi
}

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
    print_info "Detected: $DISTRO $VERSION"
}

check_system_requirements() {
    print_step "Checking system requirements..."
    
    TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_MEM" -lt 7 ]; then
        print_warning "System has ${TOTAL_MEM}GB RAM. LLM needs 8GB+ RAM."
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
    else
        print_info "RAM: ${TOTAL_MEM}GB - OK"
    fi
    
    AVAILABLE_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$AVAILABLE_SPACE" -lt 15 ]; then
        print_error "Need 15GB free disk space, have ${AVAILABLE_SPACE}GB"
        exit 1
    else
        print_info "Disk space: ${AVAILABLE_SPACE}GB - OK"
    fi
}

check_project_files() {
    print_step "Verifying project files..."
    
    local required_files=(
        "docker-compose.yml"
        "api-gateway/Dockerfile"
        "yolo-service/Dockerfile"
        "llm-service/Dockerfile"
        "postprocessor-service/Dockerfile"
    )
    
    local missing=()
    for file in "${required_files[@]}"; do
        [ ! -f "$file" ] && missing+=("$file")
    done
    
    if [ ${#missing[@]} -ne 0 ]; then
        print_error "Missing files:"
        printf '  - %s\n' "${missing[@]}"
        print_error "Run this script from project root directory!"
        exit 1
    fi
    
    print_success "All project files found"
}

install_docker() {
    print_step "Installing Docker and Docker Compose..."
    
    case $DISTRO in
        ubuntu|debian)
            sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
            sudo apt-get update
            sudo apt-get install -y ca-certificates curl gnupg lsb-release openssl
            
            sudo install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/$DISTRO/gpg | \
                sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null
            sudo chmod a+r /etc/apt/keyrings/docker.gpg
            
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
                https://download.docker.com/linux/$DISTRO $(lsb_release -cs) stable" | \
                sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
                docker-buildx-plugin docker-compose-plugin
            ;;
            
        fedora|rhel|centos)
            sudo dnf remove -y docker docker-client docker-common docker-latest \
                docker-engine 2>/dev/null || true
            sudo dnf -y install dnf-plugins-core openssl
            sudo dnf config-manager --add-repo \
                https://download.docker.com/linux/fedora/docker-ce.repo
            sudo dnf install -y docker-ce docker-ce-cli containerd.io \
                docker-buildx-plugin docker-compose-plugin
            sudo systemctl start docker
            sudo systemctl enable docker
            ;;
            
        arch|manjaro)
            sudo pacman -Sy --noconfirm docker docker-compose openssl
            sudo systemctl start docker
            sudo systemctl enable docker
            ;;
            
        *)
            print_error "Unsupported distribution: $DISTRO"
            exit 1
            ;;
    esac
    
    print_success "Docker and Docker Compose installed"
}

setup_docker_permissions() {
    print_step "Setting up Docker permissions..."
    
    if groups $USER | grep -q '\bdocker\b'; then
        print_info "User already in docker group"
    else
        sudo usermod -aG docker $USER
        print_info "Added $USER to docker group"
        print_warning "Log out and back in for changes to take effect"
    fi
}

verify_docker() {
    print_step "Verifying Docker installation..."
    
    if sg docker -c "docker --version" >/dev/null 2>&1; then
        print_info "$(sg docker -c 'docker --version')"
        print_info "$(sg docker -c 'docker compose version')"
    elif docker --version >/dev/null 2>&1; then
        print_info "$(docker --version)"
        print_info "$(docker compose version)"
    else
        print_warning "Docker installed but not accessible yet (need to re-login)"
    fi
}

setup_firebase() {
    print_step "Checking Firebase credentials..."
    
    mkdir -p api-gateway/app
    
    if [ -f "api-gateway/app/firebase_key.json" ]; then
        print_success "firebase_key.json found"
        return 0
    fi
    
    echo ""
    print_warning "firebase_key.json NOT FOUND!"
    echo ""
    echo "Options:"
    echo "  1. Paste JSON now (Ctrl+D when done)"
    echo "  2. Add manually later"
    echo ""
    read -p "Choose (1/2): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^1$ ]]; then
        print_info "Paste Firebase JSON below, then press Ctrl+D:"
        cat > api-gateway/app/firebase_key.json
        [ -s "api-gateway/app/firebase_key.json" ] && \
            print_success "Saved" || print_warning "Empty - add later"
    else
        print_warning "Add to: api-gateway/app/firebase_key.json later"
    fi
}

generate_ssl_certs() {
    print_step "Generating SSL certificates..."
    
    if [ -f "api-gateway/cert.pem" ] && [ -f "api-gateway/key.pem" ]; then
        print_info "SSL certificates already exist"
        return 0
    fi
    
    openssl req -x509 -newkey rsa:4096 -nodes \
        -out api-gateway/cert.pem \
        -keyout api-gateway/key.pem \
        -days 365 \
        -subj "/C=GB/ST=London/L=London/O=KCL/CN=localhost" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "SSL certificates generated"
        print_info "  cert.pem: api-gateway/cert.pem"
        print_info "  key.pem:  api-gateway/key.pem"
    else
        print_error "Failed to generate SSL certificates"
        exit 1
    fi
}

setup_prometheus() {
    print_step "Setting up Prometheus configuration..."
    
    mkdir -p prometheus
    
    if [ -f "prometheus/prometheus.yml" ]; then
        print_info "prometheus.yml exists - skipping"
        return 0
    fi
    
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
    
    print_success "Prometheus config created"
}

setup_grafana() {
    print_step "Setting up Grafana directories..."
    mkdir -p grafana/provisioning/datasources
    mkdir -p grafana/provisioning/dashboards
    print_success "Grafana directories created"
}

build_images() {
    print_step "Building Docker images..."
    
    echo ""
    print_warning "This takes 10-20 minutes and downloads ~10GB"
    read -p "Build now? (y/n) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Skipped - run manually: docker compose build"
        return 0
    fi
    
    print_info "Building... (this will take a while)"
    if sg docker -c "docker compose build" 2>&1 || docker compose build 2>&1; then
        print_success "Build complete"
    else
        print_error "Build failed - retry with: docker compose build"
        return 1
    fi
}

start_services() {
    print_step "Starting services..."
    
    read -p "Start all services now? (y/n) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Skipped - run manually: docker compose up -d"
        return 0
    fi
    
    if sg docker -c "docker compose up -d" 2>&1 || docker compose up -d 2>&1; then
        print_success "Services started"
        sleep 5
        sg docker -c "docker compose ps" 2>/dev/null || docker compose ps 2>/dev/null || true
    else
        print_error "Failed to start - retry with: docker compose up -d"
    fi
}

test_services() {
    print_step "Testing services..."
    sleep 3
    
    if curl -k -s https://localhost:8000/health > /dev/null 2>&1; then
        print_success "✅ API Gateway responding"
    else
        print_warning "⚠️  API Gateway not ready yet"
    fi
    
    if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
        print_success "✅ Prometheus healthy"
    else
        print_warning "⚠️  Prometheus not ready yet"
    fi
}

display_info() {
    echo ""
    print_separator
    print_success "SETUP COMPLETE!"
    print_separator
    echo ""
    echo "📡 API Gateway (HTTPS):  ${GREEN}https://localhost:8000${NC}"
    echo "   Docs:                 ${GREEN}https://localhost:8000/docs${NC}"
    echo "   Test:                 ${GREEN}curl -k https://localhost:8000/health${NC}"
    echo ""
    echo "🤖 YOLO Service:         ${GREEN}http://localhost:8001${NC}"
    echo "🧠 LLM Service:          ${GREEN}http://localhost:8002${NC}"
    echo "🗄️  MongoDB:              ${GREEN}mongodb://localhost:27017${NC}"
    echo "📬 RabbitMQ:             ${GREEN}http://localhost:15672${NC} (guest/guest)"
    echo "📊 Prometheus:           ${GREEN}http://localhost:9090${NC}"
    echo "📈 Grafana:              ${GREEN}http://localhost:3000${NC} (admin/admin)"
    echo ""
    print_separator
    echo "Useful Commands:"
    print_separator
    echo "  View logs:       ${GREEN}docker compose logs -f${NC}"
    echo "  Check status:    ${GREEN}docker compose ps${NC}"
    echo "  Restart:         ${GREEN}docker compose restart${NC}"
    echo "  Stop:            ${GREEN}docker compose down${NC}"
    echo "  Rebuild:         ${GREEN}docker compose build${NC}"
    echo ""
    
    if [ ! -f "api-gateway/app/firebase_key.json" ]; then
        print_warning "Remember to add firebase_key.json!"
        print_warning "  Location: api-gateway/app/firebase_key.json"
        print_warning "  Then run: docker compose restart api-gateway"
    fi
    
    print_separator
    echo ""
}

main() {
    clear
    echo ""
    print_separator
    echo "  ${CYAN}Cloud Computing AI SaaS - Environment Setup${NC}"
    print_separator
    echo ""
    
    check_root
    detect_distro
    check_system_requirements
    check_project_files
    
    read -p "Continue with installation? (y/n) " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 0
    
    # Install Docker if needed
    if command_exists docker; then
        print_info "Docker already installed"
    else
        install_docker
    fi
    
    setup_docker_permissions
    verify_docker
    
    # Configure project
    setup_firebase
    generate_ssl_certs
    setup_prometheus
    setup_grafana
    
    # Build and start
    build_images
    start_services
    test_services
    
    # Show info
    display_info
}

set -e
trap 'print_error "Error at line $LINENO"; exit 1' ERR

main
exit 0
