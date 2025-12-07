#!/bin/bash
# CONTINUUM Cloudflare Workers - cURL Examples

API_URL="https://your-worker.workers.dev"
TOKEN="your-jwt-token-here"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "CONTINUUM API - cURL Examples"
echo "=============================="
echo ""

# Health Check
echo -e "${BLUE}Health Check:${NC}"
curl -s "$API_URL/health" | jq '.'
echo ""

# Version
echo -e "${BLUE}Version:${NC}"
curl -s "$API_URL/version" | jq '.'
echo ""

# List Memories
echo -e "${BLUE}List Memories:${NC}"
curl -s -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/v1/memories?limit=5" | jq '.'
echo ""

# Create Memory
echo -e "${BLUE}Create Memory:${NC}"
MEMORY_ID=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test memory from cURL",
    "tags": ["test", "curl"],
    "metadata": {
      "source": "curl-example",
      "timestamp": "'$(date -Iseconds)'"
    }
  }' \
  "$API_URL/api/v1/memories" | jq -r '.data.id')

echo "Created memory with ID: $MEMORY_ID"
echo ""

# Get Memory
echo -e "${BLUE}Get Memory:${NC}"
curl -s -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/v1/memories/$MEMORY_ID" | jq '.'
echo ""

# Update Memory
echo -e "${BLUE}Update Memory:${NC}"
curl -s -X PATCH \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Updated memory content",
    "tags": ["test", "curl", "updated"]
  }' \
  "$API_URL/api/v1/memories/$MEMORY_ID" | jq '.'
echo ""

# Search
echo -e "${BLUE}Search Memories:${NC}"
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test",
    "limit": 5
  }' \
  "$API_URL/api/v1/search" | jq '.'
echo ""

# Search Suggestions
echo -e "${BLUE}Search Suggestions:${NC}"
curl -s -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/v1/search/suggest?q=test&limit=5" | jq '.'
echo ""

# Search by Tag
echo -e "${BLUE}Search by Tag:${NC}"
curl -s -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/v1/search/tags/test?limit=5" | jq '.'
echo ""

# Sync Status
echo -e "${BLUE}Sync Status:${NC}"
curl -s -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/v1/sync/status" | jq '.'
echo ""

# Delete Memory
echo -e "${BLUE}Delete Memory:${NC}"
curl -s -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/v1/memories/$MEMORY_ID" | jq '.'
echo ""

echo -e "${GREEN}Done!${NC}"
