# PulseAlpha Frontend

Premium fintech-style React frontend for AI-powered stock sentiment and prediction analysis.

## Stack

- React + Vite
- Tailwind CSS
- shadcn-style reusable UI primitives
- Recharts
- Framer Motion
- React Router
- Axios
- Lucide icons

## Run

```bash
npm install
npm run dev
```

Production build:

```bash
npm run build
```

## Routing

Public:

- /
- /market
- /company/:ticker
- /predictions
- /news
- /about

Authenticated:

- /login
- /signup
- /app
- /app/watchlist
- /app/alerts
- /app/saved-news
- /app/portfolio
- /app/settings

## API Integration

The frontend is structured for Flask REST APIs.

Configured expected endpoints:

- /api/overview
- /api/market-summary
- /api/company/:ticker
- /api/company/:ticker/news
- /api/company/:ticker/sentiment
- /api/company/:ticker/prediction
- /api/news
- /api/predictions/all
- /api/model-info
- /api/login
- /api/register
- /api/watchlist
- /api/alerts

All service modules gracefully fall back to local mock data when APIs are unavailable.

Set backend base URL with:

```bash
VITE_API_BASE_URL=http://127.0.0.1:5000
```

## Design Tokens

Palette and typography are in [src/index.css](src/index.css) using:

- Inter for UI text
- JetBrains Mono for prices and metrics

The app uses the requested dark fintech palette and responsive dashboard layout with mobile sidebar drawer.
