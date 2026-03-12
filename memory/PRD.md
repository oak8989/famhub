# Family Hub - Product Requirements Document

## Overview
Self-hosted family organization app. Single Docker container with embedded MongoDB.

## Tech Stack
- **Frontend:** React 18, Tailwind CSS (dark mode), Shadcn UI, Recharts, @zxing/library
- **Backend:** FastAPI (18 modular routers), Python 3.11, pywebpush, BeautifulSoup4
- **Database:** MongoDB 7.0 (embedded in Docker), motor 3.7.1 + pymongo 4.9+
- **Real-time:** WebSocket via FastAPI
- **Offline:** Service Worker (cache-first static, network-first API)
- **Push:** Web Push Protocol via pywebpush + VAPID keys
- **AI:** Emergent LLM (GPT-4o-mini) + OpenAI fallback
- **Scraping:** httpx with HTTP/2 + cloudscraper fallback

## All Implemented Features

### Core Modules (Full CRUD)
- [x] Calendar (+ Google Calendar sync)
- [x] Shopping List, Tasks, Notes, Grocery List, Contacts
- [x] Budget Tracker with charts + summary
- [x] Meal Planner, Recipe Box (+ URL import from 7+ recipe sites)
- [x] Pantry (barcode scanner + web lookup + auto-categorization)
- [x] Chores + Rewards + Leaderboard (gamified, points working)

### Recipe URL Import (httpx HTTP/2)
- [x] BBC Good Food, NYT Cooking, Sally's Baking, Pinch of Yum, Minimalist Baker, RecipeTin Eats, Love and Lemons
- [x] JSON-LD parser handles @type as string/list, @graph nesting, image as string/list/dict
- [x] Returns error (not blank form) when extraction fails
- [x] cloudscraper fallback for Cloudflare-protected sites

### Chores & Rewards System
- [x] Points increment on chore completion (backend verified)
- [x] Frontend displays live points from leaderboard (not stale auth context)
- [x] Reward creation + claiming with point deduction
- [x] Leaderboard shows all family members with points

### Meal → Grocery Integration
- [x] POST /api/grocery/add-from-meal/{plan_id} — compares recipe ingredients against pantry and existing grocery
- [x] Only adds missing items (fuzzy matching)
- [x] Button on meal cards in MealPlanner page

### Account Security
- [x] Change password (current + new + confirm, 6-char minimum)
- [x] Owner/Parent can reset member passwords (generates temp password)
- [x] Account tab in Settings

### Admin / Server Management (Merged into Owner Settings)
- [x] Server status dashboard, SMTP/Google/OpenAI/Server config
- [x] Test email, log viewer, server restart
- [x] Dynamic SMTP config (reads os.environ at call time, not stale imports)

### Real-time, Push & Offline
- [x] WebSocket, Push notifications, PWA, Dark mode

### Data Management
- [x] Full JSON export + CSV, Data import/restore, QR code

## Docker
- Single container: MongoDB + FastAPI, Port: 8001
- motor 3.7.1 (compatible with pymongo 4.9+)

## Backlog
- [ ] Recurring chores automation
- [ ] Multi-family hub support
- [ ] Enhance AI Meal Suggestions with dietary restrictions
- [ ] More granular dark mode theme controls
- [ ] CSS refactoring (dark mode overrides → Tailwind dark: variants)
