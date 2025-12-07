# CONTINUUM Load Testing Makefile
#
# Quick access to common load testing commands
#

.PHONY: help install quick memory search federation api web analyze clean

# Default target
help:
	@echo "CONTINUUM Load Testing Commands"
	@echo "================================"
	@echo ""
	@echo "Setup:"
	@echo "  make install    - Install dependencies"
	@echo ""
	@echo "Quick Tests:"
	@echo "  make quick      - Quick smoke test (2 min, 50 users)"
	@echo "  make web        - Launch web UI"
	@echo ""
	@echo "Scenarios:"
	@echo "  make memory     - Memory operations test (10 min, 500 users)"
	@echo "  make search     - Search operations test (5 min, 300 users)"
	@echo "  make federation - Federation test (5 min, 200 users)"
	@echo "  make api        - Full API test (10 min, 1000 users)"
	@echo "  make all        - Run all scenarios sequentially"
	@echo ""
	@echo "Analysis:"
	@echo "  make analyze    - Analyze latest test results"
	@echo "  make report     - Open latest HTML report"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean      - Remove old test results"
	@echo ""

# Install dependencies
install:
	@echo "Installing load testing dependencies..."
	pip install -r requirements.txt
	@echo "✓ Dependencies installed"

# Quick smoke test
quick:
	@echo "Running quick smoke test..."
	./run_load_tests.sh --scenario quick

# Individual scenarios
memory:
	@echo "Running memory operations test..."
	./run_load_tests.sh --scenario memory --users 500 --time 10m

search:
	@echo "Running search operations test..."
	./run_load_tests.sh --scenario search --users 300 --time 5m

federation:
	@echo "Running federation test..."
	./run_load_tests.sh --scenario federation --users 200 --time 5m

api:
	@echo "Running full API test..."
	./run_load_tests.sh --scenario api --users 1000 --time 10m

# Run all scenarios
all: memory search federation api
	@echo "✓ All scenarios complete"
	@make analyze

# Web UI
web:
	@echo "Starting Locust web UI..."
	@echo "Open http://localhost:8089 in your browser"
	./run_load_tests.sh --web

# Analysis
analyze:
	@echo "Analyzing latest test results..."
	@latest=$$(ls -t results/*_stats.csv 2>/dev/null | head -1); \
	if [ -n "$$latest" ]; then \
		./analyze_results.py "$$latest"; \
	else \
		echo "No test results found. Run a test first."; \
	fi

report:
	@echo "Opening latest HTML report..."
	@latest=$$(ls -t results/*.html 2>/dev/null | head -1); \
	if [ -n "$$latest" ]; then \
		xdg-open "$$latest" 2>/dev/null || open "$$latest" 2>/dev/null || echo "Please open: $$latest"; \
	else \
		echo "No HTML reports found. Run a test first."; \
	fi

# Cleanup
clean:
	@echo "Cleaning up old test results..."
	@count=$$(ls results/*.html results/*.csv results/*.log 2>/dev/null | wc -l); \
	if [ $$count -gt 0 ]; then \
		rm -f results/*.html results/*.csv results/*.log; \
		echo "✓ Removed $$count files"; \
	else \
		echo "No files to clean"; \
	fi

# Custom test with parameters
# Usage: make custom USERS=500 TIME=5m SCENARIO=memory
custom:
	@echo "Running custom test..."
	./run_load_tests.sh --scenario $(SCENARIO) --users $(USERS) --time $(TIME)

# Pre-release validation
validate:
	@echo "Running pre-release validation suite..."
	@echo "1/5: Quick smoke test..."
	@make quick
	@echo ""
	@echo "2/5: Memory operations..."
	@make memory
	@echo ""
	@echo "3/5: Search operations..."
	@make search
	@echo ""
	@echo "4/5: Federation..."
	@make federation
	@echo ""
	@echo "5/5: Full API test..."
	@make api
	@echo ""
	@echo "✓ Pre-release validation complete"
	@make analyze
