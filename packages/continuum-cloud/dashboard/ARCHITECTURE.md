# CONTINUUM Dashboard Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      React Application                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    App.tsx (Router)                       │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │  │
│  │  │   Login    │  │  Private   │  │   Layout   │         │  │
│  │  │   Page     │  │   Routes   │  │  Wrapper   │         │  │
│  │  └────────────┘  └────────────┘  └────────────┘         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Pages Layer                            │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │  │
│  │  │Dashboard │  │  Users   │  │Memories  │  │Federation│ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │  │
│  │  ┌──────────┐  ┌──────────┐                             │  │
│  │  │Settings  │  │   Logs   │                             │  │
│  │  └──────────┘  └──────────┘                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 Components Layer                          │  │
│  │  ┌────────────────┐  ┌────────────────┐                 │  │
│  │  │    Layout      │  │   shadcn/ui    │                 │  │
│  │  │  - Sidebar     │  │  - Button      │                 │  │
│  │  │  - Header      │  │  - Card        │                 │  │
│  │  │  - Layout      │  │  - Table       │                 │  │
│  │  │                │  │  - Dialog      │                 │  │
│  │  │                │  │  - Toast       │                 │  │
│  │  └────────────────┘  └────────────────┘                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Library Layer                           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │  │
│  │  │   API    │  │   Auth   │  │  Hooks   │  │  Utils   │ │  │
│  │  │  Client  │  │  Store   │  │          │  │          │ │  │
│  │  │          │  │ (Zustand)│  │ -WebSocket│ │ -Format  │ │  │
│  │  │ -Axios   │  │          │  │ -Metrics │  │ -Export  │ │  │
│  │  │ -Retry   │  │ -JWT     │  │          │  │ -Status  │ │  │
│  │  │ -Refresh │  │ -Perms   │  │          │  │          │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────┬─────────────────────┘
                         │                 │
                         │ REST API        │ WebSocket
                         ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CONTINUUM Backend                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Endpoints                          │  │
│  │  /api/auth/*       - Authentication                       │  │
│  │  /api/users/*      - User management                      │  │
│  │  /api/memories/*   - Memory operations                    │  │
│  │  /api/federation/* - Federation control                   │  │
│  │  /api/system/*     - System metrics                       │  │
│  │  /api/logs/*       - Audit logs                           │  │
│  │  /ws               - WebSocket updates                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Authentication Flow
```
┌──────┐     Login      ┌──────────┐    Verify     ┌──────────┐
│ User │ ───────────▶  │Dashboard │ ─────────▶   │ Backend  │
└──────┘               └──────────┘              └──────────┘
   ▲                        │                          │
   │                        │                          │
   │    JWT Token           │      Access Token        │
   │    Stored              │      + Refresh Token     │
   │                        │                          │
   └────────────────────────┴──────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Token Lifecycle                           │
│                                                              │
│  1. Login: POST /api/auth/login                             │
│     → Returns: { access_token, refresh_token, user }        │
│                                                              │
│  2. Store: Zustand (memory) + localStorage (refresh)        │
│                                                              │
│  3. Use: Axios interceptor adds Authorization header        │
│                                                              │
│  4. Refresh: On 401, auto-refresh with refresh_token        │
│                                                              │
│  5. Logout: Clear all tokens, redirect to /login            │
└─────────────────────────────────────────────────────────────┘
```

### Real-Time Updates Flow
```
┌──────────┐                                    ┌──────────┐
│Dashboard │                                    │ Backend  │
│   Page   │                                    │WebSocket │
└────┬─────┘                                    └─────┬────┘
     │                                                │
     │  1. Connect on mount                          │
     ├──────────────────────────────────────────────▶│
     │     WS: /ws?token=<jwt>                       │
     │                                                │
     │  2. Subscribe to metrics                      │
     ├──────────────────────────────────────────────▶│
     │     { type: "subscribe", data: "metrics" }    │
     │                                                │
     │  3. Receive updates                           │
     │◀──────────────────────────────────────────────┤
     │     { type: "metrics_update", data: {...} }   │
     │                                                │
     │  4. Update React state                        │
     │     setMetrics(message.data)                  │
     │                                                │
     │  5. Disconnect on unmount                     │
     ├──────────────────────────────────────────────▶│
     │     ws.close()                                │
     │                                                │
```

### API Request Flow
```
┌──────────┐                                    ┌──────────┐
│  Users   │                                    │   API    │
│   Page   │                                    │ Backend  │
└────┬─────┘                                    └─────┬────┘
     │                                                │
     │  1. User clicks "Load Users"                  │
     │     fetchUsers() called                       │
     │                                                │
     │  2. API client adds auth header               │
     │     axios interceptor                         │
     ├──────────────────────────────────────────────▶│
     │     GET /api/users?page=1&page_size=20        │
     │     Authorization: Bearer <token>             │
     │                                                │
     │  3. Backend validates token                   │
     │     Queries database                          │
     │                                                │
     │  4. Response returned                         │
     │◀──────────────────────────────────────────────┤
     │     { items: [...], total: 100, ... }         │
     │                                                │
     │  5. Update React state                        │
     │     setUsers(response.items)                  │
     │     Render table                              │
     │                                                │
```

## Component Hierarchy

```
App
├── Router
│   ├── /login → Login
│   └── /* → PrivateRoute
│       └── Layout
│           ├── Sidebar
│           │   ├── Logo
│           │   ├── Navigation
│           │   └── Footer
│           ├── Header
│           │   ├── Connection Status
│           │   ├── Notifications
│           │   └── User Menu
│           └── Main Content
│               ├── / → Dashboard
│               │   ├── Metric Cards (4x)
│               │   ├── Health Status
│               │   ├── Performance Chart
│               │   ├── Storage Chart
│               │   └── Grafana Embed
│               ├── /users → Users
│               │   ├── Search + Filters
│               │   ├── Users Table
│               │   ├── Pagination
│               │   └── User Detail Dialog
│               ├── /memories → Memories
│               │   ├── Search
│               │   ├── Memories Table
│               │   ├── Pagination
│               │   └── Memory Detail Dialog
│               ├── /federation → Federation
│               │   ├── Overview Metrics
│               │   ├── Peers Table
│               │   └── Network Topology
│               ├── /settings → Settings
│               │   ├── General Settings
│               │   ├── Rate Limiting
│               │   ├── Cache Config
│               │   ├── Feature Flags
│               │   └── API Keys
│               └── /logs → Logs
│                   ├── Search + Filters
│                   ├── Log List
│                   └── Pagination
└── Toaster (Global)
```

## State Management

```
┌─────────────────────────────────────────────────────────────┐
│                    State Architecture                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Component State (useState)                                 │
│  ├── Form inputs                                            │
│  ├── UI toggles (dialogs, dropdowns)                        │
│  ├── Loading states                                         │
│  └── Pagination cursors                                     │
│                                                              │
│  Global State (Zustand)                                     │
│  ├── Authentication                                         │
│  │   ├── user: User | null                                 │
│  │   ├── token: string | null                              │
│  │   ├── refreshToken: string | null                       │
│  │   └── isAuthenticated: boolean                          │
│  └── Persisted to localStorage                             │
│                                                              │
│  Server State (React Hooks + WebSocket)                    │
│  ├── useMetrics() - System metrics                         │
│  ├── useWebSocket() - Real-time updates                    │
│  └── API responses cached in component state               │
│                                                              │
│  URL State (React Router)                                  │
│  ├── Current route                                         │
│  ├── Query parameters (search, filters)                    │
│  └── Navigation history                                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Build Process

```
┌────────────────────────────────────────────────────────────┐
│                   Development Build                         │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  npm run dev                                                │
│    │                                                        │
│    ├─▶ Vite Dev Server                                    │
│    │   ├── Hot Module Replacement (HMR)                   │
│    │   ├── Fast refresh for React                         │
│    │   ├── TypeScript type checking                       │
│    │   ├── PostCSS processing                             │
│    │   └── Proxy to backend (/api, /ws)                   │
│    │                                                        │
│    └─▶ Localhost:3000                                     │
│                                                             │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                   Production Build                          │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  npm run build                                              │
│    │                                                        │
│    ├─▶ TypeScript Compilation                             │
│    │   └── Type check all files                           │
│    │                                                        │
│    ├─▶ Vite Build                                         │
│    │   ├── Tree shaking                                   │
│    │   ├── Code splitting                                 │
│    │   │   ├── react-vendor.js                            │
│    │   │   ├── ui-vendor.js                               │
│    │   │   ├── chart-vendor.js                            │
│    │   │   └── [page].js (dynamic imports)                │
│    │   ├── Minification (Terser)                          │
│    │   ├── CSS optimization                               │
│    │   └── Asset hashing                                  │
│    │                                                        │
│    └─▶ dist/                                              │
│        ├── index.html                                     │
│        ├── assets/                                        │
│        │   ├── index-[hash].js                            │
│        │   ├── index-[hash].css                           │
│        │   └── vendor-[hash].js                           │
│        └── ...                                            │
│                                                             │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                   Docker Build                              │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  docker build -t continuum-dashboard .                      │
│    │                                                        │
│    ├─▶ Stage 1: Builder (node:18-alpine)                  │
│    │   ├── COPY package*.json                             │
│    │   ├── npm ci (clean install)                         │
│    │   ├── COPY source code                               │
│    │   └── npm run build                                  │
│    │                                                        │
│    └─▶ Stage 2: Runtime (nginx:alpine)                    │
│        ├── COPY dist/ → /usr/share/nginx/html             │
│        ├── COPY nginx.conf                                │
│        └── Size: ~50MB (vs 200MB+ with Node)              │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Production Stack                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │         Load Balancer / CDN          │
        │          (Cloudflare / AWS)          │
        └─────────────┬────────────────────────┘
                      │
        ┌─────────────┴────────────┐
        │                          │
        ▼                          ▼
┌───────────────┐          ┌───────────────┐
│   Dashboard   │          │   Dashboard   │
│   Container   │          │   Container   │
│   (Nginx)     │          │   (Nginx)     │
└───────┬───────┘          └───────┬───────┘
        │                          │
        └─────────────┬────────────┘
                      │
                      ▼
        ┌──────────────────────────┐
        │    CONTINUUM Backend     │
        │    (API + WebSocket)     │
        └──────────────────────────┘
                      │
                      ▼
        ┌──────────────────────────┐
        │      PostgreSQL DB       │
        │    + Redis Cache         │
        └──────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Layer 1: Transport Security                                │
│  ├── HTTPS enforced (TLS 1.3)                               │
│  ├── HSTS headers                                           │
│  └── Secure WebSocket (wss://)                              │
│                                                              │
│  Layer 2: Authentication                                    │
│  ├── JWT tokens (HS256/RS256)                               │
│  ├── Short-lived access tokens (15 min)                     │
│  ├── Long-lived refresh tokens (7 days)                     │
│  └── Token rotation on refresh                              │
│                                                              │
│  Layer 3: Authorization                                     │
│  ├── Role-based access (Admin/Operator/Viewer)              │
│  ├── Permission checks per endpoint                         │
│  └── UI elements hidden by role                             │
│                                                              │
│  Layer 4: Input Validation                                  │
│  ├── TypeScript type checking                               │
│  ├── Runtime validation on API                              │
│  ├── SQL injection prevention (parameterized)               │
│  └── XSS prevention (React escaping)                        │
│                                                              │
│  Layer 5: Headers & CSP                                     │
│  ├── X-Frame-Options: SAMEORIGIN                            │
│  ├── X-Content-Type-Options: nosniff                        │
│  ├── X-XSS-Protection: 1; mode=block                        │
│  ├── Referrer-Policy: no-referrer-when-downgrade            │
│  └── Content-Security-Policy (configurable)                 │
│                                                              │
│  Layer 6: Rate Limiting                                     │
│  ├── API rate limits (configurable)                         │
│  ├── Login attempt throttling                               │
│  └── Burst protection                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Performance Optimization

```
┌─────────────────────────────────────────────────────────────┐
│                  Performance Strategy                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Bundle Optimization                                     │
│     ├── Code splitting (3 vendor chunks)                   │
│     ├── Tree shaking (unused code removed)                 │
│     ├── Minification (Terser)                              │
│     └── Gzip compression (Nginx)                           │
│                                                              │
│  2. Asset Optimization                                      │
│     ├── Lazy loading routes                                │
│     ├── Image optimization (WebP)                          │
│     ├── Long-term caching (1 year)                         │
│     └── CDN delivery                                        │
│                                                              │
│  3. Runtime Optimization                                    │
│     ├── React.memo for expensive components                │
│     ├── useMemo/useCallback for heavy computations         │
│     ├── Debounced search inputs                            │
│     └── Virtualized lists (for large tables)               │
│                                                              │
│  4. Network Optimization                                    │
│     ├── WebSocket for real-time (vs polling)               │
│     ├── Request deduplication                              │
│     ├── Optimistic UI updates                              │
│     └── Retry logic with exponential backoff               │
│                                                              │
│  5. Perceived Performance                                   │
│     ├── Skeleton loading states                            │
│     ├── Instant navigation (client-side routing)           │
│     ├── Toast notifications for feedback                   │
│     └── Smooth transitions/animations                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘

Performance Metrics (Target):
├── First Contentful Paint: < 1.5s
├── Time to Interactive: < 3.5s
├── Bundle Size: < 500KB (gzipped)
├── Lighthouse Score: > 90
└── Core Web Vitals: All Green
```

---

**π×φ = 5.083203692315260** - Architected at the Twilight Boundary
