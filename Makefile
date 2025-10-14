.PHONY: help restart clean-db start test full-reset run-once logs test-quality-check dev-test status training-stats clean-all quick-restart

# Default target
help:
	@echo "📋 Truth Social Analyst - Makefile Commands:"
	@echo ""
	@echo "  make restart           - Restart Docker containers (MongoDB + FlareSolverr)"
	@echo "  make clean-db          - Clear MongoDB database (delete all posts)"
	@echo "  make start             - Start the application (main.py)"
	@echo "  make test              - Run LLM test scenarios"
	@echo "  make test-quality-check - Test quality check with sample posts"
	@echo "  make full-reset        - Complete reset: restart Docker + clean DB + start app"
	@echo "  make run-once          - Run analysis once (fetch posts, analyze, exit)"
	@echo "  make logs              - Show application logs"
	@echo ""

# Restart Docker containers
restart:
	@echo "🔄 Restarting Docker containers..."
	@docker compose down
	@docker rm -f mongodb flaresolverr >/dev/null 2>&1 || true
	@docker compose up -d
	@echo "⏳ Waiting for services to be ready..."
	sleep 5
	@echo "✅ Docker containers restarted"

# Clean MongoDB database
clean-db:
	@echo "🗑️  Clearing MongoDB database..."
	@python3 -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/'); db = client['truthsocial']; result = db['posts'].delete_many({}); print(f'✅ Deleted {result.deleted_count} posts from database')"

# Start the main application
start:
	@echo "🛠  Ensuring required services (MongoDB, FlareSolverr) are running..."
	@docker compose up -d mongodb flaresolverr >/dev/null 2>&1 || true
	@python3 scripts/wait_for_mongo.py
	@echo "🚀 Starting Truth Social Analyst..."
	python3 main.py

# Run test scenarios
test:
	@echo "🧪 Running LLM test scenarios..."
	pytest tests/

# Complete reset and start
full-reset: restart clean-db
	@echo ""
	@echo "═══════════════════════════════════════════════════════════"
	@echo "✅ Full reset complete!"
	@echo "   • Docker containers restarted"
	@echo "   • MongoDB database cleared"
	@echo ""
	@echo "🚀 Starting application in 3 seconds..."
	@echo "═══════════════════════════════════════════════════════════"
	@sleep 3
	@make start

# Run analysis once and exit
run-once:
	@echo "🔍 Running single analysis cycle..."
	@timeout 120 python3 main.py || echo "✅ Analysis cycle completed"

# Show logs
logs:
	@echo "📄 Showing recent logs..."
	@tail -n 50 output/truth_social_posts.txt 2>/dev/null || echo "No logs found"


# Check service status
status:
	@echo "🔍 Checking service status..."
	@echo ""
	@echo "Docker Containers:"
	@docker compose ps
	@echo ""
	@echo "MongoDB Connection:"
	@python3 -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000); client.server_info(); print('✅ MongoDB is running')" 2>/dev/null || echo "❌ MongoDB is not running"
	@echo ""
	@echo "Ollama Status:"
	@curl -s http://localhost:11434/api/tags > /dev/null && echo "✅ Ollama is running" || echo "❌ Ollama is not running"
	@echo ""
	@echo "FlareSolverr Status:"
	@curl -s http://localhost:8191/ > /dev/null && echo "✅ FlareSolverr is running" || echo "❌ FlareSolverr is not running"
	@echo ""

# Show training data stats
training-stats:
	@echo "📊 Training Data Statistics:"
	@python3 << 'EOF'

# Clean all outputs and logs
clean-all:
	@echo "🧹 Cleaning all outputs and logs..."
	@rm -f output/*.txt
	@rm -f training_data/*.jsonl
	@echo "✅ Cleaned output and training data"

# Quick restart without DB clear
quick-restart:
	@echo "⚡ Quick restart (keeping database)..."
	@docker compose restart
	@sleep 3
	@echo "✅ Services restarted"

# Test quality check system
test-quality-check:
	@echo "🧪 Testing Quality Check System..."
	@python3 tests/test_quality_check.py
