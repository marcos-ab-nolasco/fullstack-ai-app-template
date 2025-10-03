#!/bin/bash
set -e

echo "🔄 Generating TypeScript types from OpenAPI spec..."

# Backend URL (default to localhost:8000, can be overridden)
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
OPENAPI_URL="${BACKEND_URL}/api/v1/openapi.json"

# Output directory and file
TYPES_DIR="app/frontend/types"
TYPES_FILE="${TYPES_DIR}/api.ts"

# Create types directory if it doesn't exist
mkdir -p "${TYPES_DIR}"

echo "📥 Fetching OpenAPI spec from ${OPENAPI_URL}..."

# Download OpenAPI spec
if ! curl -f -s "${OPENAPI_URL}" -o "${TYPES_DIR}/openapi.json"; then
  echo "❌ Error: Failed to fetch OpenAPI spec from ${OPENAPI_URL}"
  echo "   Make sure the backend is running (make dev-backend or docker-compose up)"
  exit 1
fi

echo "✨ Generating TypeScript types..."

# Generate types using openapi-typescript
cd app/frontend
pnpm dlx openapi-typescript ./types/openapi.json -o ./types/api.ts

echo "✅ Types generated successfully at ${TYPES_FILE}"
echo "🎉 You can now import types from '@/types/api'"
