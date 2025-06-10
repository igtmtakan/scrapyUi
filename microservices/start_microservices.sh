#!/bin/bash

# ScrapyUI Microservices Startup Script
# pyspider inspired architecture

set -e

echo "🚀 Starting ScrapyUI Microservices..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
SERVICES_ORDER=(
    "redis"
    "postgres" 
    "minio"
    "scheduler"
    "spider-manager"
    "result-collector"
    "api-gateway"
    "webui"
    "prometheus"
    "grafana"
    "jaeger"
    "nginx"
)

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    log_success "Dependencies check passed"
}

create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p scrapy_projects
    mkdir -p monitoring/prometheus
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/datasources
    mkdir -p nginx/ssl
    
    log_success "Directories created"
}

generate_configs() {
    log_info "Generating configuration files..."
    
    # Prometheus config
    cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'api-gateway'
    static_configs:
      - targets: ['api-gateway:8000']
    metrics_path: '/metrics'
    
  - job_name: 'scheduler'
    static_configs:
      - targets: ['scheduler:8001']
    metrics_path: '/metrics'
    
  - job_name: 'spider-manager'
    static_configs:
      - targets: ['spider-manager:8002']
    metrics_path: '/metrics'
    
  - job_name: 'result-collector'
    static_configs:
      - targets: ['result-collector:8003']
    metrics_path: '/metrics'
EOF

    # Nginx config
    cat > nginx/nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream api_gateway {
        server api-gateway:8000;
    }
    
    upstream webui {
        server webui:8004;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        # API routes
        location /api/ {
            proxy_pass http://api_gateway;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        }
        
        # WebSocket
        location /ws {
            proxy_pass http://api_gateway;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host \$host;
        }
        
        # WebUI
        location / {
            proxy_pass http://webui;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        }
    }
}
EOF

    # Database init script
    cat > init.sql << EOF
-- ScrapyUI Database Schema

CREATE TABLE IF NOT EXISTS schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    cron_expression VARCHAR(100) NOT NULL,
    project_id UUID NOT NULL,
    spider_id UUID NOT NULL,
    is_active BOOLEAN DEFAULT true,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS results (
    id VARCHAR(255) PRIMARY KEY,
    task_id UUID NOT NULL,
    data JSONB NOT NULL,
    hash VARCHAR(32) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_results_task_id ON results(task_id);
CREATE INDEX IF NOT EXISTS idx_results_hash ON results(hash);
CREATE INDEX IF NOT EXISTS idx_results_created_at ON results(created_at);

-- Insert sample data
INSERT INTO schedules (name, cron_expression, project_id, spider_id) VALUES
('Sample Schedule 1', '*/10 * * * *', gen_random_uuid(), gen_random_uuid()),
('Sample Schedule 2', '*/5 * * * *', gen_random_uuid(), gen_random_uuid())
ON CONFLICT DO NOTHING;
EOF

    log_success "Configuration files generated"
}

build_services() {
    log_info "Building Docker images..."
    
    docker-compose -f $COMPOSE_FILE build --parallel
    
    log_success "Docker images built"
}

start_infrastructure() {
    log_info "Starting infrastructure services..."
    
    # Start infrastructure first
    docker-compose -f $COMPOSE_FILE up -d redis postgres minio
    
    # Wait for services to be healthy
    log_info "Waiting for infrastructure services to be ready..."
    
    for service in redis postgres minio; do
        log_info "Waiting for $service..."
        timeout=60
        while [ $timeout -gt 0 ]; do
            if docker-compose -f $COMPOSE_FILE ps $service | grep -q "healthy\|Up"; then
                log_success "$service is ready"
                break
            fi
            sleep 2
            timeout=$((timeout-2))
        done
        
        if [ $timeout -le 0 ]; then
            log_error "$service failed to start within timeout"
            exit 1
        fi
    done
    
    log_success "Infrastructure services started"
}

start_core_services() {
    log_info "Starting core services..."
    
    # Start core services in order
    for service in scheduler spider-manager result-collector api-gateway; do
        log_info "Starting $service..."
        docker-compose -f $COMPOSE_FILE up -d $service
        
        # Wait a bit between services
        sleep 5
        
        # Check if service is running
        if docker-compose -f $COMPOSE_FILE ps $service | grep -q "Up"; then
            log_success "$service started"
        else
            log_warning "$service may have issues"
        fi
    done
    
    log_success "Core services started"
}

start_ui_and_monitoring() {
    log_info "Starting UI and monitoring services..."
    
    # Start remaining services
    docker-compose -f $COMPOSE_FILE up -d webui prometheus grafana jaeger nginx
    
    log_success "UI and monitoring services started"
}

show_status() {
    log_info "Service Status:"
    echo ""
    docker-compose -f $COMPOSE_FILE ps
    echo ""
    
    log_info "Service URLs:"
    echo -e "${GREEN}🌐 Main Application:${NC} http://localhost"
    echo -e "${GREEN}🔗 API Gateway:${NC} http://localhost:8000"
    echo -e "${GREEN}📊 Scheduler:${NC} http://localhost:8001"
    echo -e "${GREEN}🕷️ Spider Manager:${NC} http://localhost:8002"
    echo -e "${GREEN}📦 Result Collector:${NC} http://localhost:8003"
    echo -e "${GREEN}🎨 WebUI:${NC} http://localhost:8004"
    echo -e "${GREEN}📈 Prometheus:${NC} http://localhost:9090"
    echo -e "${GREEN}📊 Grafana:${NC} http://localhost:3000 (admin/admin)"
    echo -e "${GREEN}🔍 Jaeger:${NC} http://localhost:16686"
    echo -e "${GREEN}💾 MinIO:${NC} http://localhost:9001 (scrapyui/scrapyui123)"
    echo ""
}

health_check() {
    log_info "Performing health checks..."
    
    services=("api-gateway:8000" "scheduler:8001" "spider-manager:8002" "result-collector:8003")
    
    for service in "${services[@]}"; do
        name=$(echo $service | cut -d: -f1)
        port=$(echo $service | cut -d: -f2)
        
        if curl -f -s "http://localhost:$port/health" > /dev/null; then
            log_success "$name health check passed"
        else
            log_warning "$name health check failed"
        fi
    done
}

cleanup_on_exit() {
    log_info "Cleaning up on exit..."
    docker-compose -f $COMPOSE_FILE down
}

# Main execution
main() {
    # Set trap for cleanup
    trap cleanup_on_exit EXIT
    
    echo "🕷️ ScrapyUI Microservices - pyspider inspired architecture"
    echo "=================================================="
    
    check_dependencies
    create_directories
    generate_configs
    
    if [ "$1" = "--build" ]; then
        build_services
    fi
    
    start_infrastructure
    start_core_services
    start_ui_and_monitoring
    
    # Wait a bit for services to fully start
    sleep 10
    
    show_status
    health_check
    
    log_success "🎉 ScrapyUI Microservices started successfully!"
    log_info "Press Ctrl+C to stop all services"
    
    # Keep script running
    while true; do
        sleep 30
        # Optional: periodic health checks
        # health_check
    done
}

# Handle command line arguments
case "$1" in
    --build)
        main --build
        ;;
    --stop)
        log_info "Stopping all services..."
        docker-compose -f $COMPOSE_FILE down
        log_success "All services stopped"
        ;;
    --restart)
        log_info "Restarting all services..."
        docker-compose -f $COMPOSE_FILE restart
        log_success "All services restarted"
        ;;
    --logs)
        docker-compose -f $COMPOSE_FILE logs -f
        ;;
    --status)
        show_status
        ;;
    *)
        main
        ;;
esac
