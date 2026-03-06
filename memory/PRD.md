# Family Hub - Product Requirements Document

## Overview
Family Hub is a fully self-contained, self-hosted family organization app with role-based access control. It runs as a single Docker container with MongoDB embedded.

## Latest Update (December 2025)
- **New Features Implemented**:
  - ✅ AI-Powered Meal Suggestions (GPT-4o-mini via Emergent LLM)
  - ✅ QR Code for Mobile Setup
  - ✅ Push Notifications UI (Browser notifications)
  - ✅ Data Export/Backup (JSON full backup + CSV per module)
  - ✅ Manual Barcode Entry with product lookup
  - ✅ Improved Mobile Accessibility (5-item bottom nav)
  - ✅ Hidden Emergent badge on mobile
- **E2E Testing**: 100% pass rate on all 25 backend tests
- **All Modules Verified**: Calendar, Shopping, Tasks, Chores, Rewards, Notes, Budget, Meals, Recipes, Grocery, Contacts, Pantry, AI Suggestions

## Original Requirements
- Shared Calendar, Shopping List, Task List, Notes, Budget Tracker
- Meal Planner, Recipe Box, Grocery List, Contact Book
- Pantry Tracker with barcode scanner, Meal Suggestions
- Gamified Chore Chart with rewards
- User roles: Owner, Parent, Family Member, Child
- Auto-generated PINs for quick access
- Self-hostable with Docker
- Mobile-friendly (PWA)

## Implemented Features

### Authentication & User Management
- [x] Email/password registration and login
- [x] Family PIN login (6 digits, auto-generated)
- [x] Personal PIN login (4 digits, auto-generated)
- [x] Role-based permissions (Owner > Parent > Member > Child)
- [x] Add family members without email (just name + role)
- [x] Invite by email (requires SMTP configuration)

### Core Modules
- [x] Calendar with event management
- [x] Shopping List with categories
- [x] Tasks with assignment to family members
- [x] Notes with color coding
- [x] Budget with income/expense tracking and Recharts visualization
- [x] Meal Planner
- [x] Recipe Box
- [x] Grocery List
- [x] Contacts
- [x] Pantry with barcode scanner (camera + manual entry)
- [x] Meal Suggestions based on pantry (simple matching + AI-powered)

### Gamification
- [x] Chores with difficulty levels (Easy/Medium/Hard)
- [x] Points awarded on chore completion
- [x] Rewards system with point redemption
- [x] Family leaderboard

### Admin Features
- [x] Settings page with tabs (Family, Modules, Integrations, Mobile, Backup, Server)
- [x] Module enable/disable per role
- [x] Family name editing
- [x] PIN regeneration
- [x] Google Calendar sync (optional)
- [x] QR Code generation for mobile device setup
- [x] Push notifications toggle
- [x] Data export (Full JSON backup + CSV by module)

### AI Features
- [x] AI-Powered Meal Suggestions using GPT-4o-mini
- [x] Generates creative meal ideas from pantry inventory
- [x] Shows ingredients you have vs need to buy
- [x] Includes cooking tips and instructions

### Removed Features
- [x] Photo Gallery (removed per user request)
- [x] Messaging (removed per user request)

## Technical Stack
- **Frontend:** React 18, Tailwind CSS, Shadcn UI, Recharts
- **Backend:** FastAPI, Python 3.11
- **Database:** MongoDB 7.0 (embedded in Docker)
- **AI Integration:** Emergent LLM (GPT-4o-mini)
- **Process Manager:** Supervisor
- **Container:** Single self-contained Docker image

## API Endpoints (New)

### QR Code
- `GET /api/qr-code?url=...` - Returns QR code PNG
- `GET /api/qr-code/base64?url=...` - Returns base64 encoded QR

### Data Export
- `GET /api/export/data` - Full JSON backup
- `GET /api/export/csv/{module}` - CSV for specific module

### AI Suggestions
- `POST /api/suggestions/ai` - Generate AI meal ideas from pantry

### Push Notifications
- `GET /api/notifications/vapid-key` - Get VAPID public key
- `POST /api/notifications/subscribe` - Subscribe to notifications
- `DELETE /api/notifications/unsubscribe` - Unsubscribe

## Permission Matrix

| Action | Owner | Parent | Member | Child |
|--------|:-----:|:------:|:------:|:-----:|
| View all modules | ✅ | ✅ | ✅ | ✅* |
| Add/edit content | ✅ | ✅ | ✅ | ❌ |
| Add family members | ✅ | ✅ | ❌ | ❌ |
| Change settings | ✅ | ✅ | ❌ | ❌ |
| Export data | ✅ | ✅ | ✅ | ❌ |
| Server configuration | ✅ | ❌ | ❌ | ❌ |

*Module visibility configurable by admins

## Deployment
- Single Docker command: `docker run -p 8001:8001 ghcr.io/oak8989/family-hub`
- Docker Compose available for production
- Health check endpoint: `/api/health`
- Data persisted in `/data/db` volume

## Environment Variables
- `JWT_SECRET` - Required for authentication
- `EMERGENT_LLM_KEY` - Required for AI meal suggestions
- `SMTP_*` - Optional for email invitations
- `GOOGLE_*` - Optional for Google Calendar sync

## Future Enhancements (Backlog)
- [ ] Real-time WebSocket updates
- [ ] Service worker for offline support
- [ ] Recurring chores automation
- [ ] Dark mode
- [ ] Recipe import from URL
- [ ] Multiple family hub support
