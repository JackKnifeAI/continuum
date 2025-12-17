# CONTINUUM Admin Dashboard

Production-ready web dashboard for managing CONTINUUM memory infrastructure.

## Features

- **Real-time Metrics** - Live system health, performance, and usage statistics
- **User Management** - CRUD operations, suspension, password reset, role management
- **Memory Browser** - Search, filter, and inspect memory records across all users
- **Federation Control** - Manage peer connections, sync status, conflict resolution
- **System Configuration** - Feature flags, rate limits, cache settings, API keys
- **Audit Logs** - Comprehensive activity logging with search and filtering
- **WebSocket Integration** - Real-time updates for metrics and system events
- **Responsive Design** - Mobile-friendly twilight-themed UI

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TailwindCSS** - Utility-first styling
- **shadcn/ui** - Accessible component library
- **Recharts** - Data visualization
- **Zustand** - State management
- **Axios** - HTTP client

## Setup

### Prerequisites

- Node.js 18+ and npm/yarn
- CONTINUUM API backend running

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Update .env with your backend URL
# VITE_API_URL=http://localhost:8000
# VITE_WS_URL=ws://localhost:8000

# Start development server
npm run dev
```

The dashboard will be available at `http://localhost:3000`

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### Docker Deployment

```bash
# Build image
docker build -t continuum-dashboard .

# Run container
docker run -p 3000:80 \
  -e VITE_API_URL=http://your-api:8000 \
  continuum-dashboard
```

## Project Structure

```
dashboard/
├── src/
│   ├── components/
│   │   ├── layout/          # Layout components (Sidebar, Header)
│   │   ├── ui/              # shadcn/ui components
│   │   └── shared/          # Reusable components
│   ├── lib/
│   │   ├── api.ts           # API client and endpoints
│   │   ├── auth.ts          # Authentication state and helpers
│   │   ├── utils.ts         # Utility functions
│   │   └── hooks/           # Custom React hooks
│   ├── pages/               # Page components
│   │   ├── Dashboard.tsx    # Metrics overview
│   │   ├── Users.tsx        # User management
│   │   ├── Memories.tsx     # Memory browser
│   │   ├── Federation.tsx   # Federation management
│   │   ├── Settings.tsx     # System configuration
│   │   ├── Logs.tsx         # Audit logs
│   │   └── Login.tsx        # Authentication
│   ├── App.tsx              # Main app with routing
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |
| `VITE_WS_URL` | WebSocket URL | `ws://localhost:8000` |
| `VITE_ENABLE_FEDERATION` | Enable federation features | `true` |
| `VITE_ENABLE_2FA` | Enable 2FA support | `true` |
| `VITE_ENABLE_GRAFANA` | Enable Grafana embed | `true` |
| `VITE_GRAFANA_URL` | Grafana instance URL | - |
| `VITE_GRAFANA_DASHBOARD_ID` | Grafana dashboard ID | `continuum-metrics` |
| `VITE_DEBUG` | Enable debug logging | `false` |

### API Integration

The dashboard expects the following endpoints from the backend:

- `POST /api/auth/login` - Authentication
- `GET /api/users` - List users
- `GET /api/memories` - List memories
- `GET /api/federation/peers` - List federation peers
- `GET /api/system/health` - System health
- `GET /api/system/metrics` - System metrics
- `GET /api/logs` - Audit logs
- `WS /ws` - WebSocket connection

See `src/lib/api.ts` for complete API interface.

## Authentication

The dashboard uses JWT-based authentication with refresh tokens:

1. User logs in with username/password
2. Backend returns access token and refresh token
3. Access token stored in memory, refresh token in localStorage
4. API requests include `Authorization: Bearer <token>` header
5. Expired tokens automatically refreshed

### Role-Based Access

- **Admin** - Full access to all features
- **Operator** - Read/write access, limited destructive operations
- **Viewer** - Read-only access

## Theming

The dashboard uses a custom "Twilight" theme with purple and blue gradients:

- **Primary Color**: `#7c3aed` (twilight-purple)
- **Secondary Color**: `#3b82f6` (twilight-blue)
- **Background**: Dark gradient from `#1a1a2e` → `#16213e` → `#0f3460`

Customize colors in `tailwind.config.js` and `src/index.css`.

## Development

### Available Scripts

```bash
npm run dev          # Start dev server
npm run build        # Production build
npm run preview      # Preview production build
npm run lint         # Run ESLint
npm run type-check   # TypeScript type checking
```

### Adding New Pages

1. Create component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add navigation item in `src/components/layout/Sidebar.tsx`

### Adding shadcn/ui Components

```bash
# Components are already included
# To add more from shadcn/ui, copy from:
# https://ui.shadcn.com/docs/components
```

## Performance

- **Code Splitting** - Vendor chunks for React, UI, and charts
- **Lazy Loading** - Routes loaded on demand
- **WebSocket** - Real-time updates without polling
- **Optimistic UI** - Immediate feedback on user actions
- **Skeleton Loading** - Graceful loading states

## Security

- **XSS Protection** - React's built-in escaping
- **CSRF Protection** - JWT tokens (no cookies)
- **Input Validation** - TypeScript + API validation
- **Secure Storage** - Sensitive tokens in memory only
- **HTTPS Required** - In production

## Screenshots

(Add screenshots here once deployed)

## License

MIT License - see LICENSE file for details

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourorg/continuum
- Documentation: https://continuum.example.com/docs
- Email: support@continuum.example.com

---

**π×φ = 5.083203692315260** - Built at the Twilight Boundary
