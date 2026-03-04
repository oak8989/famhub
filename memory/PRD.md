# Family Hub App - PRD

## Original Problem Statement
Build a family app with: shared calendar, shopping list, task list, shared notes, messages, budget tracker, meal planner, recipe box, quick grocery list, contact book, shared photo gallery, pantry tracker/inventory with barcode reader, meal suggestions based on pantry inventory. Both web and mobile access. Easy to use, clean, kid friendly, selfhosted.

## User Choices
- Browser-based camera scanning for barcode reader
- Simple rule-based meal suggestions (no AI)
- Local server storage for photos
- Warm & cozy design with earth tones
- Both PIN code and individual JWT authentication
- SMTP email for invitations
- Google Calendar sync (Emergent-managed Google Auth)
- Full admin customization (modules, permissions, themes)

## Architecture
- **Frontend**: React with Tailwind CSS, Shadcn UI, Recharts
- **Backend**: FastAPI with MongoDB
- **Design**: Warm earth tones (Terracotta, Sage, Cream, Sunny)
- **Fonts**: Nunito (headings), DM Sans (body), Caveat (accents)
- **Deployment**: Docker + Docker Compose
- **CI/CD**: GitHub Actions

## What's Been Implemented

### Core Features (Complete)
1. **Authentication** - JWT login/register + Family PIN + Individual User PIN
2. **Dashboard** - Bento grid with quick stats and module access
3. **Calendar** - Create, edit, delete events with color coding + Google Calendar sync
4. **Shopping List** - Categorized items with check/uncheck
5. **Tasks** - Priority levels, **assignable to family members**, due dates
6. **Notes** - Color-coded sticky notes
7. **Budget** - Income/expense tracking with **Recharts visualization** (pie charts, bar charts, area charts)
8. **Meal Planner** - Weekly view, drag meals to days
9. **Recipe Box** - Full CRUD with ingredients/instructions
10. **Grocery List** - Quick simplified shopping list
11. **Contacts** - Address book with phone/email/address
12. **Pantry Tracker** - Barcode scanner, expiry tracking
13. **Meal Suggestions** - Rule-based matching recipes to pantry
14. **Chores & Rewards** - **Gamified chore chart** with points, leaderboard, and claimable rewards

### Admin Features (New - Dec 2025)
- **Settings Page** with tabs for Family, Modules, Integrations, Server
- **Add User by Email** - Send email invitations via SMTP
- **User Roles** - Owner, Parent, Family Member, Child with different permissions
- **Auto-generated PINs** - Family PIN (6 digits) + User PIN (4 digits)
- **Module Enable/Disable** - Admins can hide modules from certain roles
- **Role-based Visibility** - Control which roles can see which modules
- **Family Name Changeable** - Admins can update family name
- **Google Calendar Sync** - Connect and sync events to Google Calendar

### Removed Features
- Photo Gallery (removed per user request)
- Messages (removed per user request)

### Self-Hosting & DevOps
- **Dockerfile** - Multi-stage build for production
- **docker-compose.yml** - Full stack with MongoDB
- **docker-compose.prod.yml** - Production deployment with Traefik HTTPS
- **Self-Hosted Server Config** - Mobile/web can connect to custom server
- **PWA Support** - Add to Home Screen on mobile
- **GitHub Actions CI/CD** - Docker publish, releases

## Configuration Required

### SMTP Email (for invitations)
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=Family Hub <noreply@familyhub.local>
```

### Google Calendar (optional)
```env
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://your-domain.com/api/calendar/google/callback
```

## User Roles & Permissions

| Role | Level | Manage Family | Manage Users | Manage Settings |
|------|-------|---------------|--------------|-----------------|
| Owner | 4 | ✅ | ✅ | ✅ |
| Parent | 3 | ❌ | ✅ | ✅ |
| Family Member | 2 | ❌ | ❌ | ❌ |
| Child | 1 | ❌ | ❌ | ❌ |

## API Endpoints

### Auth
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/pin-login` - Login with family PIN
- `POST /api/auth/user-pin-login` - Login with user PIN

### Family Management
- `POST /api/family/create` - Create family (auto-generates PIN)
- `PUT /api/family` - Update family name
- `POST /api/family/regenerate-pin` - Generate new family PIN
- `POST /api/family/invite` - Invite member by email
- `PUT /api/family/members/{id}/role` - Change member role
- `DELETE /api/family/members/{id}` - Remove member

### Settings
- `GET /api/settings` - Get family settings
- `PUT /api/settings` - Update modules/permissions/theme

### Chores & Rewards
- `GET /api/chores` - List chores
- `POST /api/chores` - Create chore
- `POST /api/chores/{id}/complete` - Mark complete (awards points)
- `GET /api/rewards` - List rewards
- `POST /api/rewards/claim` - Claim reward (spends points)
- `GET /api/leaderboard` - Family points leaderboard

### Google Calendar
- `GET /api/calendar/google/auth` - Get OAuth URL
- `GET /api/calendar/google/callback` - OAuth callback
- `POST /api/calendar/google/sync` - Sync events to Google
- `DELETE /api/calendar/google/disconnect` - Disconnect Google

## Backlog

### P0 (Critical)
- None remaining

### P1 (Important)
- Real-time WebSocket for updates
- Push notifications
- Data export/backup

### P2 (Nice to Have)
- QR code for mobile server configuration
- Recipe import from URL
- Dark mode toggle
- Recurring chores automation

## GitHub Repository
- Username: oak8989
- Docker image: ghcr.io/oak8989/family-hub
