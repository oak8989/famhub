# Family Hub App - PRD

## Original Problem Statement
Build a family app with: shared calendar, shopping list, task list, shared notes, messages, budget tracker, meal planner, recipe box, quick grocery list, contact book, shared photo gallery, pantry tracker/inventory with barcode reader, meal suggestions based on pantry inventory. Both web and mobile access. Easy to use, clean, kid friendly, selfhosted.

## User Choices
- Browser-based camera scanning for barcode reader
- Simple rule-based meal suggestions (no AI)
- Local server storage for photos
- Warm & cozy design with earth tones
- Both PIN code and individual JWT authentication

## Architecture
- **Frontend**: React with Tailwind CSS, Shadcn UI components
- **Backend**: FastAPI with MongoDB
- **Design**: Warm earth tones (Terracotta, Sage, Cream, Sunny)
- **Fonts**: Nunito (headings), DM Sans (body), Caveat (accents)

## What's Been Implemented (Feb 2, 2026)

### Core Features
1. **Authentication** - JWT login/register + Family PIN access
2. **Dashboard** - Bento grid with quick stats and module access
3. **Calendar** - Create, edit, delete events with color coding
4. **Shopping List** - Categorized items with check/uncheck
5. **Tasks** - Priority levels, assignment, due dates
6. **Notes** - Color-coded sticky notes
7. **Messages** - Family chat with real-time polling
8. **Budget** - Income/expense tracking with summary
9. **Meal Planner** - Weekly view, drag meals to days
10. **Recipe Box** - Full CRUD with ingredients/instructions
11. **Grocery List** - Quick simplified shopping list
12. **Contacts** - Address book with phone/email/address
13. **Photo Gallery** - Local storage, upload, view, delete
14. **Pantry Tracker** - Barcode scanner, expiry tracking
15. **Meal Suggestions** - Rule-based matching recipes to pantry

### Technical Implementation
- Full CRUD APIs for all modules
- MongoDB collections for all data
- JWT authentication with bcrypt password hashing
- File upload for photos
- @zxing/library for barcode scanning
- Responsive mobile-first design

## Backlog

### P0 (Critical)
- None remaining

### P1 (Important)
- Real-time WebSocket for messages
- Push notifications
- Data export/backup

### P2 (Nice to Have)
- Recipe import from URL
- Shared grocery list sync
- Family member roles/permissions
- Dark mode toggle
