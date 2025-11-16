# Trading System - Makefile
# Easy management of Docker-based trading system

.PHONY: help up down restart logs build clean test init

# Default target
help:
	@echo "Trading System - Make Commands"
	@echo "=============================="
	@echo ""
	@echo "  make init       - Initialize system (first time setup)"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - View logs (all services)"
	@echo "  make build      - Build all Docker images"
	@echo "  make clean      - Stop and remove all containers/volumes"
	@echo "  make test       - Run all tests"
	@echo "  make status     - Show service status"
	@echo ""
	@echo "Individual Services:"
	@echo "  make logs-ingestion   - View market data ingestion logs"
	@echo "  make logs-signals     - View signal processor logs"
	@echo "  make logs-executor    - View trade executor logs"
	@echo "  make logs-risk        - View risk monitor logs"
	@echo "  make logs-dashboard   - View dashboard logs"
	@echo ""
	@echo "Data & Cache:"
	@echo "  make redis-cli        - Connect to Redis CLI"
	@echo "  make psql             - Connect to PostgreSQL/TimescaleDB"
	@echo "  make kafka-topics     - List Kafka topics"
	@echo ""

# Initialize system (first time)
init:
	@echo "Initializing Trading System..."
	@mkdir -p logs data config/environments sql
	@echo "Creating environment file..."
	@if [ ! -f .env ]; then \
		echo "PYTHONUNBUFFERED=1" > .env; \
		echo "TZ=Asia/Kolkata" >> .env; \
		echo ".env file created"; \
	fi
	@echo "Building Docker images..."
	@docker-compose build
	@echo ""
	@echo "✓ Initialization complete!"
	@echo "  Run 'make up' to start the system"

# Start all services
up:
	@echo "Starting Trading System..."
	@docker-compose up -d
	@echo ""
	@echo "✓ All services started!"
	@echo "  Dashboard: http://localhost:8050"
	@echo "  Use 'make logs' to view logs"
	@echo "  Use 'make status' to check health"

# Stop all services
down:
	@echo "Stopping Trading System..."
	@docker-compose down
	@echo "✓ All services stopped"

# Restart all services
restart:
	@echo "Restarting Trading System..."
	@docker-compose restart
	@echo "✓ Services restarted"

# View logs
logs:
	@docker-compose logs -f --tail=100

# Individual service logs
logs-ingestion:
	@docker-compose logs -f --tail=100 market_data_ingestion

logs-signals:
	@docker-compose logs -f --tail=100 signal_processor

logs-executor:
	@docker-compose logs -f --tail=100 trade_executor

logs-risk:
	@docker-compose logs -f --tail=100 risk_monitor

logs-dashboard:
	@docker-compose logs -f --tail=100 dashboard

# Build all images
build:
	@echo "Building Docker images..."
	@docker-compose build --no-cache
	@echo "✓ Build complete"

# Clean everything (CAUTION: deletes all data)
clean:
	@echo "⚠️  WARNING: This will delete all containers and data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "Cleaning..."; \
		docker-compose down -v; \
		rm -rf logs/* data/*.db; \
		echo "✓ Cleanup complete"; \
	else \
		echo "Cancelled"; \
	fi

# Show service status
status:
	@echo "Service Status:"
	@echo "==============="
	@docker-compose ps
	@echo ""
	@echo "Health Checks:"
	@echo "=============="
	@docker ps --format "table {{.Names}}\t{{.Status}}" | grep trading

# Run tests
test:
	@echo "Running tests..."
	@docker-compose exec -T market_data_ingestion python -m pytest tests/ -v
	@echo "✓ Tests complete"

# Redis CLI
redis-cli:
	@docker-compose exec redis redis-cli

# PostgreSQL/TimescaleDB CLI
psql:
	@docker-compose exec timescaledb psql -U trading -d trading_data

# List Kafka topics
kafka-topics:
	@docker-compose exec kafka kafka-topics.sh --bootstrap-server localhost:9092 --list

# View Kafka messages (market data)
kafka-market-data:
	@docker-compose exec kafka kafka-console-consumer.sh \
		--bootstrap-server localhost:9092 \
		--topic trading.market_data \
		--from-beginning \
		--max-messages 10

# View Kafka messages (signals)
kafka-signals:
	@docker-compose exec kafka kafka-console-consumer.sh \
		--bootstrap-server localhost:9092 \
		--topic trading.signals \
		--from-beginning \
		--max-messages 10

# Backup database
backup:
	@echo "Creating backup..."
	@mkdir -p backups
	@docker-compose exec -T timescaledb pg_dump -U trading trading_data > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✓ Backup created in backups/ directory"

# Restore database
restore:
	@echo "⚠️  This will restore from latest backup"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		LATEST=$$(ls -t backups/*.sql | head -1); \
		echo "Restoring from $$LATEST..."; \
		docker-compose exec -T timescaledb psql -U trading trading_data < $$LATEST; \
		echo "✓ Restore complete"; \
	fi

# Install Python dependencies
deps:
	@echo "Installing Python dependencies..."
	@pip install -r requirements.txt
	@echo "✓ Dependencies installed"

# Run locally (without Docker)
run-local:
	@echo "Running locally..."
	@python -m src.workers.market_data_worker

# Quick start (for daily use)
start: up
	@echo ""
	@echo "🚀 Trading System is running!"
	@echo "   Dashboard: http://localhost:8050"
	@sleep 2
	@make status

# Quick stop
stop: down
	@echo "Trading System stopped"
