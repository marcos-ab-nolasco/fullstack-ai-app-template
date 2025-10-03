# CLAUDE.md - Monorepo Template Build Specification

> **Purpose:** This document provides complete context and progressive build instructions for constructing a production-ready monorepo template with FastAPI backend, Next.js frontend, PostgreSQL, Redis, and AI integration.

## Project Context

### Objective
Build a fully functional monorepo template for rapid project initialization, featuring authentication, chat interface, and multi-provider AI integration (OpenAI, Anthropic, Gemini, Grok). This is a personal template designed for solo development with emphasis on development velocity and performance.

### Core Requirements
- **Backend:** FastAPI with Python 3.11+, type-safe, async-first
- **Frontend:** Next.js 14+ with App Router, TypeScript, Tailwind CSS
- **Database:** PostgreSQL for relational data, Redis for cache/sessions
- **AI Integration:** Abstract service layer supporting multiple providers
- **Development:** Docker Compose for local orchestration, Makefile for commands
- **Type Safety:** OpenAPI contract between backend and frontend

### Non-Goals (For Initial Version)
- Kubernetes deployment (Docker Compose only)
- Production environment configuration (dev-focused)
- Multi-tenant architecture
- Microservices beyond single backend
- Advanced observability (basic logging sufficient)

---

## Architecture Overview

### Monorepo Structure
```
monorepo-template/
├── app/
│   ├── backend/          # FastAPI application
│   └── frontend/         # Next.js application
├── infrastructure/
│   ├── docker/
│   └── docker-compose.yml
├── scripts/
├── Makefile
├── turbo.json
├── pnpm-workspace.yaml
└── CLAUDE.md (this file)
```

### Technology Stack

**Backend:**
- FastAPI + Uvicorn
- SQLAlchemy 2.0 + Alembic (migrations)
- Pydantic V2 (validation)
- python-jose (JWT)
- passlib + bcrypt (password hashing)
- httpx (async HTTP client)
- redis-py (async)
- openai, anthropic SDKs

**Frontend:**
- Next.js 14 (App Router)
- TypeScript 5+
- Tailwind CSS + shadcn/ui
- openapi-fetch + openapi-typescript
- Zustand (state management)
- React Hook Form + Zod

**Infrastructure:**
- PostgreSQL 16
- Redis 7
- Docker + Docker Compose
- pnpm (package manager)
- Turborepo (task orchestration)

---

## Progressive Build Roadmap

### Phase 1: Foundation & Backend Core
**Goal:** Functional backend with database, authentication, and health checks.

#### Features:
1. **Project Structure**
   - Create monorepo folder structure
   - Configure pnpm workspaces
   - Setup Turborepo configuration
   - Create root Makefile with essential commands

2. **Backend Application**
   - Initialize FastAPI app with proper structure (api/, core/, db/, schemas/, services/)
   - Configure Pydantic Settings for environment management
   - Setup CORS, middleware stack
   - Implement `/health_check` endpoint
   - Generate OpenAPI documentation at `/docs`

3. **Database Layer**
   - PostgreSQL connection with SQLAlchemy async
   - Alembic migrations setup
   - Create User model (id, email, hashed_password, full_name, created_at, updated_at)
   - Database session management with dependency injection

4. **Authentication System**
   - Password hashing with bcrypt
   - JWT token generation (access + refresh)
   - Auth endpoints: POST /auth/register, POST /auth/login, POST /auth/refresh, POST /auth/logout
   - Protected route dependency (get_current_user)
   - Token blacklist in Redis (optional for Phase 1)

5. **Docker Compose - Backend Services**
   - PostgreSQL service with health check
   - Redis service with health check
   - Backend service with proper dependencies
   - Volume mounts for development

#### Validation Checkpoints:
- [ ] `make setup` initializes project successfully
- [ ] `make dev-backend` starts backend on localhost:8000
- [ ] `/docs` shows OpenAPI interface with auth endpoints
- [ ] Can register user via POST /auth/register
- [ ] Can login and receive JWT token
- [ ] Protected endpoints reject requests without valid token
- [ ] Database persists data between container restarts

---

### Phase 2: Frontend Foundation & Auth Integration
**Goal:** Working Next.js app with complete authentication flow.

#### Features:
1. **Frontend Project Setup**
   - Initialize Next.js with TypeScript
   - Configure Tailwind CSS
   - Install and setup shadcn/ui
   - Create base layout structure

2. **Type Generation Pipeline**
   - Script to download OpenAPI spec from backend
   - Generate TypeScript types with openapi-typescript
   - Update turbo.json to include generate-types task
   - Add Makefile command: `make generate-types`

3. **API Client Layer**
   - Create typed API client with openapi-fetch
   - Implement auth API functions (register, login, logout, refresh)
   - HTTP interceptor for token injection
   - Automatic token refresh on 401

4. **State Management**
   - Zustand store for auth state (user, token, isAuthenticated)
   - Persist auth state to localStorage
   - Auto-rehydrate on app load

5. **Auth Pages**
   - /login page with form (email, password)
   - /register page with form (email, password, full_name)
   - Form validation with React Hook Form + Zod
   - Error handling and loading states
   - Redirect after successful auth

6. **Protected Routes**
   - Next.js middleware for auth checking
   - Redirect unauthenticated users to /login
   - Redirect authenticated users from /login to /dashboard

7. **Docker Compose - Frontend Service**
   - Add frontend service to docker-compose.yml
   - Configure hot reload for development
   - Proxy API requests to backend (via NEXT_PUBLIC_API_URL)

#### Validation Checkpoints:
- [ ] `make generate-types` creates apps/frontend/src/types/api.ts
- [ ] `make dev` starts both backend and frontend
- [ ] Frontend accessible at localhost:3000
- [ ] Can register new user from /register page
- [ ] Can login from /login page and see token in state
- [ ] Protected /dashboard route redirects to /login when unauthenticated
- [ ] Token persists across page refreshes
- [ ] Logout clears token and redirects to /login

---

### Phase 3: Chat Data Models & Backend API
**Goal:** Complete chat backend with conversation and message management.

#### Features:
1. **Database Models**
   - Conversation model (id, user_id, title, ai_provider, ai_model, system_prompt, created_at, updated_at)
   - Message model (id, conversation_id, role, content, tokens_used, metadata JSONB, created_at)
   - Proper foreign keys and indexes
   - Alembic migration for new tables

2. **Chat Schemas (Pydantic)**
   - ConversationCreate, ConversationRead, ConversationUpdate
   - MessageCreate, MessageRead
   - ChatRequest, ChatResponse (for streaming)

3. **Chat Endpoints**
   - POST /chat/conversations - Create new conversation
   - GET /chat/conversations - List user's conversations
   - GET /chat/conversations/{id} - Get conversation details
   - DELETE /chat/conversations/{id} - Delete conversation
   - POST /chat/conversations/{id}/messages - Send message (non-streaming first)
   - GET /chat/conversations/{id}/messages - List conversation messages

4. **Business Logic**
   - Service layer for conversation management
   - Message validation and sanitization
   - Authorization checks (user can only access own conversations)

#### Validation Checkpoints:
- [ ] Migration creates conversations and messages tables
- [ ] Can create conversation via API
- [ ] Can list conversations (filtered by current user)
- [ ] Can send message to conversation (stores in DB)
- [ ] Cannot access other user's conversations (403 Forbidden)
- [ ] OpenAPI docs updated with new endpoints

---

### Phase 4: AI Service Layer (Non-Streaming)
**Goal:** Working AI integration with multiple providers, non-streaming responses.

#### Features:
1. **AI Service Architecture**
   - Abstract base class `BaseAIService` with interface
   - Factory pattern for provider selection
   - Providers: OpenAIService, AnthropicService, (GeminiService, GrokService optional)

2. **Configuration**
   - Environment variables for API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY)
   - Settings validation with Pydantic
   - Default model selection per provider

3. **Service Implementation**
   - Implement `generate_response(messages, model, **kwargs) -> str`
   - Error handling for API failures
   - Retry logic with exponential backoff (using tenacity)
   - Token counting and usage tracking

4. **Chat Controller Integration**
   - Modify POST /chat/conversations/{id}/messages to use AI service
   - Select provider based on conversation.ai_provider
   - Store AI response as message in database
   - Return both user message and AI response

5. **System Prompt Support**
   - Use conversation.system_prompt if provided
   - Default system prompt if none specified
   - Include system message in context sent to AI

#### Validation Checkpoints:
- [ ] Can send message and receive AI response (OpenAI)
- [ ] Response stored in database with role='assistant'
- [ ] Can switch providers by changing conversation.ai_provider
- [ ] API errors handled gracefully (return 502 with error message)
- [ ] System prompt influences AI responses
- [ ] Token usage tracked in message.tokens_used

---

### Phase 5: Frontend Chat Interface
**Goal:** Complete chat UI with conversation management and message display.

#### Features:
1. **Chat Store (Zustand)**
   - Current conversation state
   - Messages list
   - Loading states
   - Actions: createConversation, sendMessage, fetchMessages, selectConversation

2. **Chat Components**
   - `ConversationList` - Sidebar with conversation list
   - `ConversationItem` - Single conversation entry
   - `ChatInterface` - Main chat container
   - `MessageList` - Display conversation messages
   - `MessageBubble` - Individual message (user/assistant styling)
   - `MessageInput` - Text input with send button

3. **Chat Page Layout**
   - /dashboard/chat route
   - Sidebar + main content layout (responsive)
   - Empty state when no conversation selected
   - Create new conversation button

4. **Message Flow**
   - Send message → optimistic update → API call → update with response
   - Scroll to bottom on new message
   - Loading indicator while AI responds
   - Error handling with retry option

5. **Markdown Rendering**
   - Install react-markdown + remark-gfm
   - Render AI responses with markdown support
   - Code syntax highlighting (optional: react-syntax-highlighter)

6. **Conversation Management**
   - Create new conversation modal/form
   - Select provider and model
   - Edit conversation title
   - Delete conversation with confirmation

#### Validation Checkpoints:
- [ ] Can create new conversation from UI
- [ ] Can switch between conversations
- [ ] Messages display correctly (user right, assistant left)
- [ ] Send message shows loading state
- [ ] AI response appears after processing
- [ ] Markdown renders properly (bold, lists, code blocks)
- [ ] Can delete conversation
- [ ] UI responsive on mobile and desktop

---

### Phase 6: Streaming Responses
**Goal:** Real-time streaming of AI responses for better UX.

#### Features:
1. **Backend Streaming**
   - New endpoint: POST /chat/conversations/{id}/messages/stream
   - Use Server-Sent Events (SSE) or streaming response
   - Implement `generate_response_stream()` in AI services
   - Yield tokens as they arrive from AI provider
   - Final message with `[DONE]` marker

2. **Frontend Streaming Consumer**
   - Implement EventSource or fetch with readable stream
   - Update message content as tokens arrive
   - Handle connection errors and reconnection
   - Display "AI is typing..." indicator

3. **Optimistic Updates**
   - Add user message to UI immediately
   - Add empty assistant message with loading indicator
   - Stream tokens into assistant message
   - Save complete message to backend after stream completes

#### Validation Checkpoints:
- [ ] Messages stream in real-time (visible token-by-token)
- [ ] No UI freezing during streaming
- [ ] Connection errors handled gracefully
- [ ] Complete message saved to DB after stream ends
- [ ] Can interrupt stream (stop generation button)

---

### Phase 7: Redis Cache & Performance
**Goal:** Optimize performance with caching and rate limiting.

#### Features:
1. **Redis Integration**
   - Async Redis client configuration
   - Cache middleware for GET endpoints
   - Custom key serialization function
   - TTL configuration per endpoint

2. **HTTP Caching**
   - Cache conversation list (5 minutes TTL)
   - Cache message history (10 minutes TTL)
   - Invalidate cache on create/update/delete
   - Cache OpenAPI spec (1 hour TTL)

3. **Rate Limiting**
   - Implement slowapi rate limiter
   - Per-user rate limits (e.g., 10 messages/minute)
   - Per-IP rate limits for auth endpoints
   - Return 429 with Retry-After header

4. **Session Management**
   - Store active sessions in Redis
   - Token blacklist for logout
   - Session expiration cleanup

5. **Frontend Optimizations**
   - React.memo for expensive components
   - useMemo for computed values
   - useCallback for event handlers
   - Debounce input fields
   - Virtual scrolling for long message lists (optional)

#### Validation Checkpoints:
- [ ] Repeated GET requests served from cache (check logs)
- [ ] Cache invalidates on data changes
- [ ] Rate limiting triggers on excessive requests
- [ ] Logged out users cannot use tokens (blacklisted)
- [ ] Frontend remains responsive with 100+ messages

---

### Phase 8: Production-Ready Polish
**Goal:** Complete Docker setup, documentation, and deployment readiness.

#### Features:
1. **Complete Docker Compose**
   - All services with health checks
   - Proper startup order (depends_on with condition)
   - Volume mounts for data persistence
   - Environment variable management
   - Network isolation

2. **Database Seeding**
   - Script to create test users
   - Sample conversations and messages
   - `make seed-db` command

3. **Makefile Completion**
   - All essential commands documented
   - `make help` with descriptions
   - Database management commands (migrate, reset, backup)
   - Testing commands
   - Linting and formatting commands

4. **Environment Configuration**
   - Complete .env.example files (root, backend, frontend)
   - Documentation for each variable
   - Validation on startup

5. **Comprehensive README**
   - Architecture overview with diagram
   - Quick start guide (3 commands to run)
   - Development workflow
   - Customization guide
   - Troubleshooting section
   - API documentation link

6. **Testing Setup**
   - Backend: pytest with fixtures for DB and auth
   - Frontend: Vitest for unit tests
   - Basic test coverage for critical paths
   - `make test` runs all tests

7. **Logging & Monitoring**
   - Structured logging (JSON format)
   - Request/response logging
   - Error tracking with stack traces
   - Performance metrics (response time, token usage)

#### Validation Checkpoints:
- [ ] `make setup` → `make dev` → fully functional app (cold start)
- [ ] All services start with health checks passing
- [ ] `make seed-db` populates test data
- [ ] `make test` passes all tests
- [ ] README provides clear onboarding path
- [ ] Can customize template (rename, change providers) easily
- [ ] Logs provide useful debugging information

---

## Development Conventions

### Code Style
- **Python:** Black (line length 100), Ruff, mypy strict mode
- **TypeScript:** ESLint, Prettier, strict TypeScript config
- **Commits:** Conventional commits (feat:, fix:, docs:, etc.)

### File Naming
- **Backend:** snake_case for files and functions
- **Frontend:** PascalCase for components, camelCase for utilities
- **Tests:** test_*.py (backend), *.test.ts (frontend)

### Error Handling
- Always return proper HTTP status codes
- Structured error responses: `{"detail": [{"msg": "error message"}]}`
- Log errors with context (user_id, request_id)
- Never expose sensitive information in errors

### Security
- Hash passwords with bcrypt (cost factor 12)
- Validate and sanitize all inputs
- Use parameterized queries (SQLAlchemy prevents SQL injection)
- CORS configured for specific origins (not "*" in production)
- Rate limit authentication endpoints

### Performance
- Use async/await consistently
- Index foreign keys and frequently queried columns
- Paginate list endpoints (default 20 items)
- Cache expensive operations
- Lazy load frontend components
