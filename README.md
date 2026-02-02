# Family Hub

<p align="center">
  <img src="https://img.shields.io/badge/Docker-Ready-blue?logo=docker" alt="Docker Ready">
  <img src="https://img.shields.io/badge/Self--Hosted-Yes-green" alt="Self-Hosted">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="MIT License">
  <img src="https://img.shields.io/github/v/release/yourusername/family-hub?include_prereleases" alt="Release">
</p>

<p align="center">
  <strong>🏠 Your Family's Digital Home</strong><br>
  A comprehensive, self-hosted family organization app
</p>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📅 **Calendar** | Shared family events with color coding |
| 🛒 **Shopping List** | Collaborative lists with categories |
| ✅ **Tasks** | Assign chores with priorities & due dates |
| 📝 **Notes** | Color-coded family notes |
| 💬 **Messages** | Family chat |
| 💰 **Budget** | Track income & expenses |
| 🍽️ **Meal Planner** | Plan weekly meals |
| 📖 **Recipe Box** | Store & organize recipes |
| 🥬 **Grocery List** | Quick shopping list |
| 👥 **Contacts** | Family address book |
| 📷 **Photos** | Shared photo gallery |
| 📦 **Pantry** | Inventory with barcode scanner |
| 💡 **Meal Ideas** | Suggestions based on pantry |

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/family-hub.git
cd family-hub

# Configure environment
cp .env.example .env
nano .env  # Edit JWT_SECRET

# Start the application
docker-compose up -d

# Access at http://localhost:8001
```

### Option 2: Pull from GitHub Container Registry

```bash
# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  family-hub:
    image: ghcr.io/yourusername/family-hub:latest
    ports:
      - "8001:8001"
    environment:
      - MONGO_URL=mongodb://mongo:27017
      - DB_NAME=family_hub
      - JWT_SECRET=your-secret-key-here
    depends_on:
      - mongo
  mongo:
    image: mongo:7
    volumes:
      - mongo-data:/data/db
volumes:
  mongo-data:
EOF

# Start
docker-compose up -d
```

## 📱 Mobile Setup

Family Hub works great on mobile devices:

### Add to Home Screen

**iOS Safari:**
1. Open Family Hub URL
2. Tap Share button (□↑)
3. Select "Add to Home Screen"

**Android Chrome:**
1. Open Family Hub URL
2. Tap menu (⋮)
3. Select "Add to Home screen"

### Connect to Self-Hosted Server

1. Open the app
2. Tap **"Self-Hosted Server"** on login screen
3. Enter your server URL (e.g., `https://family.yourdomain.com`)
4. Tap **"Test Connection"**
5. Save and login

## 🔐 Authentication

Family Hub supports two authentication methods:

| Method | Best For |
|--------|----------|
| **Family PIN** | Quick access for all family members |
| **Individual Account** | Personal login with email/password |

### First-Time Setup

1. Go to **Account** tab → Register
2. Create your account
3. After login, create a Family
4. Set a **Family PIN** (e.g., `1234`)
5. Share the PIN with family members

## 🌐 Production Deployment

### With Traefik (HTTPS)

```bash
# Configure environment
cp .env.example .env
nano .env

# Set these values:
# JWT_SECRET=your-random-secret
# DOMAIN=family.yourdomain.com
# ACME_EMAIL=your@email.com

# Deploy with HTTPS
docker-compose -f docker-compose.prod.yml up -d
```

### With Nginx

```nginx
server {
    listen 80;
    server_name family.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name family.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 50M;
    }
}
```

## 🔧 Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET` | Secret for JWT tokens | *Required* |
| `MONGO_URL` | MongoDB connection URL | `mongodb://mongo:27017` |
| `DB_NAME` | Database name | `family_hub` |
| `PORT` | Application port | `8001` |
| `CORS_ORIGINS` | Allowed origins | `*` |

## 💾 Backup & Restore

### Backup

```bash
# Backup MongoDB
docker exec family-hub-mongo mongodump --out /data/backup
docker cp family-hub-mongo:/data/backup ./backup-$(date +%Y%m%d)

# Backup photos
docker cp family-hub:/app/backend/photos ./photos-backup-$(date +%Y%m%d)
```

### Restore

```bash
# Restore MongoDB
docker cp ./backup-20240101 family-hub-mongo:/data/backup
docker exec family-hub-mongo mongorestore /data/backup

# Restore photos
docker cp ./photos-backup-20240101/. family-hub:/app/backend/photos/
```

## 🛠️ Development

```bash
# Clone repository
git clone https://github.com/yourusername/family-hub.git
cd family-hub

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload --port 8001

# Frontend (new terminal)
cd frontend
yarn install
yarn start
```

## 📄 License

MIT License - feel free to use, modify, and distribute!

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

<p align="center">
  Made with ❤️ for families everywhere
</p>
