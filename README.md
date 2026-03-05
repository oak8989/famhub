# Family Hub 🏠

<p align="center">
  <img src="https://img.shields.io/badge/Docker-Self--Contained-blue?logo=docker" alt="Docker">
  <img src="https://img.shields.io/badge/MongoDB-Included-green?logo=mongodb" alt="MongoDB">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="MIT License">
</p>

<p align="center">
  <strong>Your Family's Digital Home</strong><br>
  A fully self-contained, self-hosted family organization app with role-based access control
</p>

---

## ✨ Features

### Core Modules
| Module | Description |
|--------|-------------|
| 📅 **Calendar** | Shared family events with Google Calendar sync |
| 🛒 **Shopping List** | Collaborative shopping lists with categories |
| ✅ **Tasks** | Assignable tasks with priorities & due dates |
| 🏆 **Chores & Rewards** | Gamified chore chart with points & leaderboard |
| 📝 **Notes** | Color-coded family notes |
| 💰 **Budget** | Income/expense tracking with visual charts |
| 🍽️ **Meal Planner** | Weekly meal planning |
| 📖 **Recipe Box** | Store & organize family recipes |
| 🥬 **Grocery List** | Quick shopping list |
| 👥 **Contacts** | Family address book |
| 📦 **Pantry** | Inventory tracking with barcode scanner |
| 💡 **Meal Ideas** | Recipe suggestions based on pantry |

### Admin Features
- **User Management** - Add family members with auto-generated PINs
- **Role-Based Access** - Owner, Parent, Family Member, Child roles
- **Module Control** - Enable/disable modules per role
- **Theme Customization** - Customize colors and appearance
- **Google Calendar Sync** - Sync events to Google Calendar

---

## 🚀 Quick Start

### One Command Deploy (Recommended)

Everything runs in ONE container - MongoDB included!

```bash
docker run -d \
  --name family-hub \
  -p 8001:8001 \
  -v family-hub-data:/data/db \
  -e JWT_SECRET=your-secret-key-change-me \
  ghcr.io/oak8989/family-hub:latest
```

**Access at:** http://localhost:8001

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  family-hub:
    image: ghcr.io/oak8989/family-hub:latest
    container_name: family-hub
    ports:
      - "8001:8001"
    volumes:
      - family-hub-data:/data/db
    environment:
      - JWT_SECRET=change-this-to-a-secure-random-string
      # Optional: Email invitations
      # - SMTP_HOST=smtp.gmail.com
      # - SMTP_PORT=587
      # - SMTP_USER=your-email@gmail.com
      # - SMTP_PASSWORD=your-app-password
    restart: unless-stopped

volumes:
  family-hub-data:
```

```bash
docker-compose up -d
```

### Build from Source

```bash
git clone https://github.com/oak8989/family-hub.git
cd family-hub
docker build -t family-hub .
docker run -d -p 8001:8001 -e JWT_SECRET=mysecret family-hub
```

---

## 👥 User Roles & Permissions

| Permission | Owner | Parent | Member | Child |
|------------|:-----:|:------:|:------:|:-----:|
| Use all modules | ✅ | ✅ | ✅ | ✅* |
| Add family members | ✅ | ✅ | ❌ | ❌ |
| Change family name | ✅ | ✅ | ❌ | ❌ |
| Manage settings | ✅ | ✅ | ❌ | ❌ |
| Server configuration | ✅ | ❌ | ❌ | ❌ |
| Create rewards | ✅ | ✅ | ❌ | ❌ |

*Child access can be customized per module by admins

---

## 🔐 Authentication

### PIN-Based Login (Quick Access)

- **Family PIN** (6 digits) - Shared PIN for quick family access (guest/child role)
- **Personal PIN** (4 digits) - Individual PIN that preserves your role

### Account Login

- Email/password authentication with JWT tokens

### First-Time Setup

1. Click "Create an account" on the login page
2. Register with your name, email, and password
3. After login, click "Create a new family hub"
4. Your family is created with an auto-generated 6-digit PIN
5. You become the **Owner** with full admin access

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description | Default |
|----------|:--------:|-------------|---------|
| `JWT_SECRET` | **Yes** | Secret key for JWT tokens | - |
| `DB_NAME` | No | MongoDB database name | `family_hub` |
| `CORS_ORIGINS` | No | Allowed CORS origins | `*` |

### Email Invitations (Optional)

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=Family Hub <noreply@example.com>
```

### Google Calendar Sync (Optional)

```env
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://your-domain.com/api/calendar/google/callback
```

---

## 📱 Mobile Setup

Family Hub works great as a Progressive Web App (PWA):

### iOS
1. Open Family Hub in Safari
2. Tap Share button (□↑)
3. Select "Add to Home Screen"

### Android
1. Open Family Hub in Chrome
2. Tap menu (⋮)
3. Select "Add to Home Screen"

### Self-Hosted Server
On the login page, click "Self-Hosted Server" to enter your server URL.

---

## 💾 Data Persistence

Data is stored in Docker volumes:

| Volume | Path | Purpose |
|--------|------|---------|
| `family-hub-data` | `/data/db` | MongoDB database |

### Backup

```bash
# Create backup
docker run --rm \
  -v family-hub-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/family-hub-backup.tar.gz /data

# Restore backup
docker run --rm \
  -v family-hub-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/family-hub-backup.tar.gz -C /
```

---

## 🏥 Health Check

The container includes an automatic health check:

```bash
curl http://localhost:8001/api/health
# Returns: {"status":"healthy"}
```

---

## 🛠️ Tech Stack

- **Frontend:** React, Tailwind CSS, Shadcn UI, Recharts
- **Backend:** FastAPI, Python 3.11
- **Database:** MongoDB 7.0 (embedded)
- **Process Manager:** Supervisor

---

## 📄 API Endpoints

<details>
<summary>Click to expand API documentation</summary>

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Email/password login
- `POST /api/auth/pin-login` - Family PIN login
- `POST /api/auth/user-pin-login` - Personal PIN login

### Family Management
- `POST /api/family/create` - Create family (auto-generates PIN)
- `GET /api/family` - Get family info
- `PUT /api/family` - Update family name
- `GET /api/family/members` - List family members
- `POST /api/family/add-member` - Add member (returns PIN)
- `PUT /api/family/members/{id}/role` - Change member role
- `DELETE /api/family/members/{id}` - Remove member
- `POST /api/family/regenerate-pin` - Generate new family PIN

### Settings
- `GET /api/settings` - Get family settings
- `PUT /api/settings` - Update settings (modules, permissions, theme)
- `GET /api/settings/server` - Server config (owner only)

### Modules
All modules follow REST conventions:
- `GET /api/{module}` - List items
- `POST /api/{module}` - Create item
- `PUT /api/{module}/{id}` - Update item
- `DELETE /api/{module}/{id}` - Delete item

Modules: `calendar`, `shopping`, `tasks`, `chores`, `notes`, `budget`, `meals`, `recipes`, `grocery`, `contacts`, `pantry`

### Chores & Rewards
- `POST /api/chores/{id}/complete` - Complete chore (awards points)
- `GET /api/rewards` - List rewards
- `POST /api/rewards` - Create reward
- `POST /api/rewards/claim` - Claim reward (deducts points)
- `GET /api/leaderboard` - Family points leaderboard

</details>

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

<p align="center">
  Made with ❤️ for families everywhere<br>
  <sub>Built with React, FastAPI, MongoDB</sub>
</p>
