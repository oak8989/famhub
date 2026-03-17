# Famhub - Product Requirements Document

## Original Problem Statement
Build a full-stack, self-hostable application for families called "Famhub" (formerly "Family Hub") with shared calendar, shopping list, task list, shared notes, budget tracker, meal planner, recipe box, grocery list, contact book, pantry tracker, chore system with gamification, and more.

## Tech Stack
- **Frontend:** React, Tailwind CSS, Shadcn UI, Axios, Recharts, PWA (Service Workers)
- **Backend:** FastAPI (modular), MongoDB (embedded), WebSockets, pywebpush, httpx
- **Auth:** JWT (72h expiration, rate-limited endpoints)
- **DevOps:** Docker, Supervisor

## Core Features (All Implemented)
- Shared Calendar (with per-user Google Calendar two-way sync)
- Shopping List, Task List (assignable), Shared Notes
- Budget Tracker (with visualization charts)
- Meal Planner (with AI suggestions), Recipe Box (with URL import)
- Quick Grocery List, Contact Book
- Pantry Tracker with barcode scanner + Bulk Scan mode
- Chore System with gamification & rewards + claim history
- **In Case of Emergency (NOK Box)** - Emergency contacts, medical info, vehicles, documents, custom notes with file attachments
- **Household Inventory** - Track items by category, location, condition with barcode scanner & OpenFoodFacts lookup, bulk add
- Settings with user management (Owner, Parent, Member, Child roles)
- Dark Mode, PWA offline support, push notifications
- Data export/import, QR code setup
- Email invites with pending invite management
- Password change, owner reset, forgot password with email reset link
- Server URL configuration in admin panel
- Security: JWT expiration, rate limiting, dynamic config
- **Module Visibility (Family-level)**: Owner/Parent can enable/disable modules and control which roles see them
- **Module Visibility (Personal)**: Each user can personally show/hide modules via Settings > Account > My Modules
- Settings merge: GET /api/settings merges stored settings with DEFAULT_FAMILY_SETTINGS so new modules always appear

## Key API Endpoints
- `/api/nok-box/*` - Full CRUD for Emergency Info + file upload/serve
- `/api/inventory/*` - Full CRUD + bulk-add + barcode lookup
- `PUT /api/auth/hidden-modules` - Store user's personal hidden module preferences
- `/api/settings` - Module visibility settings (merged with defaults)
- `/api/auth/*` - Register, login, forgot/reset password
- `/api/calendar/google/*` - Per-user Google OAuth & two-way sync
- Full CRUD for all other modules
- `/api/admin/*` - Server management (Owner only)

## Integrations
- Emergent LLM Key / emergentintegrations (AI Meal Suggestions)
- OpenAI GPT (fallback for self-hosted)
- Emergent-managed Google Auth (per-user Calendar sync)
- pywebpush (push notifications)
- OpenFoodFacts API (barcode lookup for Pantry & Inventory)

## Critical Notes
- motor==3.4.0 and pymongo<4.7 pinned in requirements.txt
- Backend uses dynamic config pattern for all env-based settings
- JWT tokens expire after 72 hours
- Rate limiting: 10 attempts per 5 minutes on auth endpoints
- Dockerfile secrets removed from ENV (passed at runtime)

## Testing Status (March 17, 2026)
- Module visibility (personal + admin): Backend 18/18, Frontend 11/11 — iteration_19.json
- NOK Box & Inventory CRUD: Backend 26/26, Frontend 25/25 — iteration_18.json
- All previous features tested in iterations 13-16

## Upcoming / Future Tasks
- P2: Enhanced AI Meal Suggestions (dietary restrictions, recent meals)
- P2: More granular dark mode theme controls
- P3: Refactor App.css dark mode overrides to Tailwind dark: variants
- P3: Module reordering (drag-and-drop sidebar arrangement)
