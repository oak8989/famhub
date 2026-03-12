# Family Hub - Product Requirements Document

## Original Problem Statement
Build a full-stack, self-hostable application for families called "Family Hub" with shared calendar, shopping list, task list, shared notes, budget tracker, meal planner, recipe box, grocery list, contact book, pantry tracker, chore system with gamification, and more.

## Tech Stack
- **Frontend:** React, Tailwind CSS, Shadcn UI, Axios, Recharts, PWA (Service Workers)
- **Backend:** FastAPI (modular), MongoDB (embedded), WebSockets, pywebpush, httpx
- **Auth:** JWT
- **DevOps:** Docker, Supervisor

## Core Features (All Implemented)
- Shared Calendar (with Google Calendar sync)
- Shopping List
- Task List (assignable)
- Shared Notes
- Budget Tracker (with visualization charts)
- Meal Planner (with AI suggestions)
- Recipe Box (with URL import)
- Quick Grocery List
- Contact Book
- Pantry Tracker with barcode scanner + **Bulk Scan mode**
- Chore System with gamification & rewards + claim history
- Settings with user management (Owner, Parent, Member, Child roles)
- Dark Mode, PWA offline support, push notifications
- Data export/import, QR code setup
- Email invites with pending invite management
- Password change & owner reset

## Completed Features (Latest Session - March 2026)
- **Quantity Placeholder "0"**: Shopping, Grocery, and Pantry quantity inputs now show placeholder "0" instead of "Qty" or being pre-filled
- **Bulk Pantry Scanning**: New full-screen bulk scanning mode on Pantry page with continuous barcode scanning, temporary review list with edit/remove, and batch save via `POST /api/pantry/bulk-add`

## Previously Completed (Prior Sessions)
- Admin Portal merged into main app Settings
- Docker crash fix (motor/pymongo pin)
- Mobile UI/UX fixes
- Dynamic SMTP/Google config
- Recipe import overhaul (httpx)
- Password management
- Chore system bug fixes
- Meal-to-Grocery feature
- Pending invite management
- Reward claim history

## Key API Endpoints
- `POST /api/pantry/bulk-add` - Bulk add pantry items (new)
- `POST /api/auth/register`, `POST /api/auth/login`
- `POST /api/auth/change-password`, `POST /api/auth/reset-password`
- Full CRUD for: shopping, grocery, pantry, tasks, notes, budget, meals, recipes, contacts, calendar, chores, rewards
- `POST /api/recipes/import-url`
- `POST /api/meal-plans/{id}/add-missing-to-grocery`
- `GET /api/reward-claims`
- `/api/admin/*` - Server management (Owner only)

## Database Collections
- users, families, family_settings
- shopping_items, grocery_items, pantry_items
- tasks, notes, calendar_events
- budget_entries, meal_plans, recipes
- contacts, chores, rewards, reward_claims
- push_subscriptions

## Integrations
- Emergent LLM Key / emergentintegrations (AI Meal Suggestions)
- OpenAI GPT (fallback for self-hosted)
- Emergent-managed Google Auth (Calendar sync)
- pywebpush (push notifications)

## Critical Notes
- motor==3.4.0 and pymongo<4.7 pinned in requirements.txt (Docker crash prevention)
- Backend uses dynamic config pattern for SMTP/Google/OpenAI settings
- All backend routes prefixed with /api

## Upcoming / Future Tasks
- P2: Enhanced AI Meal Suggestions (dietary restrictions, recent meals)
- P2: More granular dark mode theme controls
- P3: Refactor App.css dark mode overrides to Tailwind dark: variants
