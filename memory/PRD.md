# Family Hub - Product Requirements Document

## Original Problem Statement
Build a full-stack, self-hostable application for families called "Family Hub" with shared calendar, shopping list, task list, shared notes, budget tracker, meal planner, recipe box, grocery list, contact book, pantry tracker, chore system with gamification, and more.

## Tech Stack
- **Frontend:** React, Tailwind CSS, Shadcn UI, Axios, Recharts, PWA (Service Workers)
- **Backend:** FastAPI (modular), MongoDB (embedded), WebSockets, pywebpush, httpx
- **Auth:** JWT (72h expiration, rate-limited endpoints)
- **DevOps:** Docker, Supervisor

## Core Features (All Implemented)
- Shared Calendar (with Google Calendar sync)
- Shopping List, Task List (assignable), Shared Notes
- Budget Tracker (with visualization charts)
- Meal Planner (with AI suggestions), Recipe Box (with URL import)
- Quick Grocery List, Contact Book
- Pantry Tracker with barcode scanner + Bulk Scan mode
- Chore System with gamification & rewards + claim history
- Settings with user management (Owner, Parent, Member, Child roles)
- Dark Mode, PWA offline support, push notifications
- Data export/import, QR code setup
- Email invites with pending invite management
- Password change, owner reset, forgot password with email reset link
- Server URL configuration in admin panel
- Security: JWT expiration, rate limiting, dynamic config
- **Module Visibility Enforcement**: Sidebar, dashboard, and routes filter modules based on role+visibility settings

## Latest Changes (March 2026)
- **Module Visibility Bug Fix**: Settings module visibility (visible_to per role) was not enforced. Now:
  - AuthContext loads `familySettings` and exposes `isModuleVisible(key)`
  - Layout sidebar filters nav items based on user role + module visibility
  - Dashboard filters stat cards, quick actions, and module grid tiles
  - App.js routes redirect hidden modules to /dashboard via `ModuleRoute`
  - Owner always sees everything; settings changes take effect immediately

## Key API Endpoints
- `GET /api/settings` - Get family settings including module visibility
- `PUT /api/settings` - Update module visibility (owner only)
- `POST /api/auth/forgot-password`, `POST /api/auth/reset-password-token`
- `POST /api/pantry/bulk-add` - Bulk add pantry items
- Full CRUD for all modules
- `/api/admin/*` - Server management (Owner only)

## Integrations
- Emergent LLM Key / emergentintegrations (AI Meal Suggestions)
- OpenAI GPT (fallback for self-hosted)
- Emergent-managed Google Auth (Calendar sync)
- pywebpush (push notifications)

## Critical Notes
- motor==3.4.0 and pymongo<4.7 pinned in requirements.txt
- Backend uses dynamic config pattern for all env-based settings
- JWT tokens expire after 72 hours
- Rate limiting: 10 attempts per 5 minutes on auth endpoints
- Dockerfile secrets removed from ENV (passed at runtime)

## Upcoming / Future Tasks
- P2: Enhanced AI Meal Suggestions (dietary restrictions, recent meals)
- P2: More granular dark mode theme controls
- P3: Refactor App.css dark mode overrides to Tailwind dark: variants
