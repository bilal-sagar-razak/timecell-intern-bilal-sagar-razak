.PHONY: install install-backend install-frontend dev dev-backend dev-frontend test test-backend test-frontend test-e2e refresh-amfi clean

install: install-backend install-frontend

install-backend:
	pip install -r backend/requirements.txt

install-frontend:
	cd frontend && npm install --no-fund --no-audit
	cd frontend && npx playwright install chromium

dev:
	@echo "Starting backend on :8000 + frontend on :3000..."
	@$(MAKE) -j 2 dev-backend dev-frontend

dev-backend:
	cd backend && uvicorn main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test: test-backend test-frontend

test-backend:
	cd backend && python -m pytest -v

test-frontend:
	cd frontend && npm test

test-e2e:
	cd frontend && npm run test:e2e

refresh-amfi:
	cd backend && python -m scripts.refresh_amfi

clean:
	find backend -name __pycache__ -exec rm -rf {} +
	rm -rf backend/.pytest_cache backend/.ruff_cache
	rm -rf frontend/.next frontend/test-results frontend/playwright-report
