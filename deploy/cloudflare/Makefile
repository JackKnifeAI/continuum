# CONTINUUM Cloudflare Workers - Makefile

.PHONY: help install dev build deploy clean test lint format

help:
	@echo "CONTINUUM Cloudflare Workers - Available commands:"
	@echo ""
	@echo "  make install       Install dependencies"
	@echo "  make dev          Start local development server"
	@echo "  make build        Build the worker"
	@echo "  make deploy       Deploy to production"
	@echo "  make deploy-dev   Deploy to development"
	@echo "  make deploy-staging  Deploy to staging"
	@echo "  make test         Run tests"
	@echo "  make lint         Lint code"
	@echo "  make format       Format code"
	@echo "  make clean        Clean build artifacts"
	@echo "  make kv-create    Create KV namespaces"
	@echo "  make tail         Stream live logs"
	@echo ""

install:
	npm install

dev:
	npm run dev

build:
	npm run build

deploy:
	npm run deploy:prod

deploy-dev:
	npm run deploy:dev

deploy-staging:
	npm run deploy:staging

test:
	npm test

lint:
	npm run lint

format:
	npm run format

clean:
	rm -rf dist/ node_modules/ .wrangler/

kv-create:
	@echo "Creating KV namespaces..."
	wrangler kv:namespace create CACHE
	wrangler kv:namespace create CACHE --preview
	wrangler kv:namespace create SESSIONS
	wrangler kv:namespace create SESSIONS --preview
	@echo ""
	@echo "Update wrangler.toml with the namespace IDs shown above"

tail:
	wrangler tail

secret-jwt:
	@echo "Generating JWT secret..."
	@JWT_SECRET=$$(openssl rand -base64 32); \
	echo "Generated secret: $$JWT_SECRET"; \
	echo "$$JWT_SECRET" | wrangler secret put JWT_SECRET

secret-list:
	wrangler secret list

type-check:
	npm run type-check

all: install build deploy
