"""
Family Hub - Server Admin Portal
Runs on port 8050 for server administration
Uses session-based form login (works in all browsers)
"""

from fastapi import FastAPI, HTTPException, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
import os
import secrets
import subprocess
import json
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv, set_key

ROOT_DIR = Path(__file__).parent
ENV_FILE = ROOT_DIR / '.env'
load_dotenv(ENV_FILE)

app = FastAPI(title="Family Hub Admin Portal", docs_url=None, redoc_url=None)

SESSION_SECRET = os.environ.get('ADMIN_SESSION_SECRET', secrets.token_hex(32))
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'familyhub')


def require_login(request: Request):
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=302, headers={"Location": "/login"})


class SMTPConfig(BaseModel):
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

class GoogleConfig(BaseModel):
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""

class OpenAIConfig(BaseModel):
    openai_api_key: str = ""

class ServerConfig(BaseModel):
    jwt_secret: str = ""
    cors_origins: str = "*"
    db_name: str = "family_hub"


def get_env_value(key: str, default: str = "") -> str:
    return os.environ.get(key, default)

def save_env_value(key: str, value: str):
    if ENV_FILE.exists():
        set_key(str(ENV_FILE), key, value)
    os.environ[key] = value


LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Family Hub Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Inter', sans-serif; }</style>
</head>
<body class="bg-gray-900 min-h-screen flex items-center justify-center">
    <div class="w-full max-w-sm mx-4">
        <div class="bg-gray-800 rounded-2xl p-8 border border-gray-700 shadow-xl">
            <div class="text-center mb-8">
                <h1 class="text-2xl font-bold text-orange-400">Family Hub</h1>
                <p class="text-gray-400 text-sm mt-1">Admin Portal</p>
            </div>
            {{ERROR_MSG}}
            <form method="POST" action="/login" class="space-y-5">
                <div>
                    <label class="block text-sm text-gray-400 mb-1">Username</label>
                    <input type="text" name="username" required autofocus
                        class="w-full px-4 py-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500">
                </div>
                <div>
                    <label class="block text-sm text-gray-400 mb-1">Password</label>
                    <input type="password" name="password" required
                        class="w-full px-4 py-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500">
                </div>
                <button type="submit"
                    class="w-full py-2.5 bg-orange-500 hover:bg-orange-600 text-white rounded-lg font-medium transition-colors">
                    Sign In
                </button>
            </form>
        </div>
    </div>
</body>
</html>"""

ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Family Hub - Admin Portal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .toast { animation: slideIn 0.3s ease-out; }
        @keyframes slideIn { from { transform: translateY(-100%); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
    </style>
</head>
<body class="bg-gray-900 text-white min-h-screen">
    <div id="toast" class="fixed top-4 right-4 hidden toast"></div>
    <div class="max-w-6xl mx-auto p-6">
        <div class="flex items-center justify-between mb-8 pb-4 border-b border-gray-700">
            <div>
                <h1 class="text-3xl font-bold text-orange-400">Family Hub</h1>
                <p class="text-gray-400">Server Administration Portal</p>
            </div>
            <div class="flex gap-3">
                <button onclick="checkStatus()" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg flex items-center gap-2 text-sm">
                    Check Status
                </button>
                <button onclick="rebootServer()" class="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg flex items-center gap-2 text-sm">
                    Restart Server
                </button>
                <a href="/logout" class="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg text-sm">Logout</a>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div class="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <div class="text-gray-400 text-sm">Backend Status</div>
                <div id="backend-status" class="text-xl font-bold text-yellow-400">Checking...</div>
            </div>
            <div class="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <div class="text-gray-400 text-sm">Database</div>
                <div id="db-status" class="text-xl font-bold text-yellow-400">Checking...</div>
            </div>
            <div class="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <div class="text-gray-400 text-sm">Email (SMTP)</div>
                <div id="smtp-status" class="text-xl font-bold text-yellow-400">Checking...</div>
            </div>
            <div class="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <div class="text-gray-400 text-sm">OpenAI</div>
                <div id="openai-status" class="text-xl font-bold text-yellow-400">Checking...</div>
            </div>
        </div>

        <div class="flex gap-2 mb-6 border-b border-gray-700">
            <button onclick="showTab('email')" id="tab-email" class="tab-btn px-4 py-2 border-b-2 border-orange-500 text-orange-400">Email Setup</button>
            <button onclick="showTab('google')" id="tab-google" class="tab-btn px-4 py-2 border-b-2 border-transparent text-gray-400 hover:text-white">Google Calendar</button>
            <button onclick="showTab('openai')" id="tab-openai" class="tab-btn px-4 py-2 border-b-2 border-transparent text-gray-400 hover:text-white">OpenAI</button>
            <button onclick="showTab('server')" id="tab-server" class="tab-btn px-4 py-2 border-b-2 border-transparent text-gray-400 hover:text-white">Server Config</button>
            <button onclick="showTab('logs')" id="tab-logs" class="tab-btn px-4 py-2 border-b-2 border-transparent text-gray-400 hover:text-white">Logs</button>
        </div>

        <!-- Email Setup -->
        <div id="panel-email" class="tab-panel bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h2 class="text-xl font-bold mb-4">Email (SMTP) Configuration</h2>
            <p class="text-gray-400 mb-6">Configure SMTP settings to enable email invitations for family members.</p>
            <form id="smtp-form" class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">SMTP Host</label>
                        <input type="text" name="smtp_host" id="smtp_host" placeholder="smtp.gmail.com" class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:border-orange-500 focus:outline-none text-white">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">SMTP Port</label>
                        <input type="number" name="smtp_port" id="smtp_port" value="587" class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:border-orange-500 focus:outline-none text-white">
                    </div>
                </div>
                <div>
                    <label class="block text-sm text-gray-400 mb-1">SMTP Username</label>
                    <input type="text" name="smtp_user" id="smtp_user" placeholder="your-email@gmail.com" class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:border-orange-500 focus:outline-none text-white">
                </div>
                <div>
                    <label class="block text-sm text-gray-400 mb-1">SMTP Password</label>
                    <input type="password" name="smtp_password" id="smtp_password" placeholder="App password" class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:border-orange-500 focus:outline-none text-white">
                    <p class="text-xs text-gray-500 mt-1">For Gmail, use an App Password (not your regular password)</p>
                </div>
                <div>
                    <label class="block text-sm text-gray-400 mb-1">From Email</label>
                    <input type="text" name="smtp_from" id="smtp_from" placeholder="Family Hub <noreply@familyhub.local>" class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:border-orange-500 focus:outline-none text-white">
                </div>
                <div class="flex gap-3">
                    <button type="submit" class="px-6 py-2 bg-orange-500 hover:bg-orange-600 rounded-lg font-medium">Save SMTP Settings</button>
                    <button type="button" onclick="testEmail()" class="px-6 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg">Test Connection</button>
                </div>
            </form>
        </div>

        <!-- Google Calendar -->
        <div id="panel-google" class="tab-panel hidden bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h2 class="text-xl font-bold mb-4">Google Calendar API</h2>
            <p class="text-gray-400 mb-6">Enable Google Calendar sync for family events.</p>
            <div class="bg-blue-900/30 border border-blue-700 rounded-lg p-4 mb-6">
                <p class="text-blue-300 text-sm">
                    <strong>Setup Instructions:</strong><br>
                    1. Go to <a href="https://console.cloud.google.com/apis/credentials" target="_blank" class="underline">Google Cloud Console</a><br>
                    2. Create OAuth 2.0 credentials<br>
                    3. Set redirect URI to: <code class="bg-blue-800 px-1 rounded">{your-domain}/api/calendar/google/callback</code>
                </p>
            </div>
            <form id="google-form" class="space-y-4">
                <div>
                    <label class="block text-sm text-gray-400 mb-1">Google Client ID</label>
                    <input type="text" name="google_client_id" id="google_client_id" placeholder="xxx.apps.googleusercontent.com" class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:border-blue-500 focus:outline-none text-white">
                </div>
                <div>
                    <label class="block text-sm text-gray-400 mb-1">Google Client Secret</label>
                    <input type="password" name="google_client_secret" id="google_client_secret" class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:border-blue-500 focus:outline-none text-white">
                </div>
                <div>
                    <label class="block text-sm text-gray-400 mb-1">Redirect URI</label>
                    <input type="text" name="google_redirect_uri" id="google_redirect_uri" placeholder="https://your-domain.com/api/calendar/google/callback" class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:border-blue-500 focus:outline-none text-white">
                </div>
                <button type="submit" class="px-6 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg font-medium">Save Google Settings</button>
            </form>
        </div>

        <!-- OpenAI -->
        <div id="panel-openai" class="tab-panel hidden bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h2 class="text-xl font-bold mb-4">OpenAI Configuration</h2>
            <p class="text-gray-400 mb-6">Enable AI-powered meal suggestions based on pantry items.</p>
            <form id="openai-form" class="space-y-4">
                <div>
                    <label class="block text-sm text-gray-400 mb-1">OpenAI API Key</label>
                    <input type="password" name="openai_api_key" id="openai_api_key" placeholder="sk-..." class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:border-green-500 focus:outline-none text-white">
                    <p class="text-xs text-gray-500 mt-1">Get your API key from <a href="https://platform.openai.com/api-keys" target="_blank" class="underline">OpenAI Platform</a></p>
                </div>
                <button type="submit" class="px-6 py-2 bg-green-500 hover:bg-green-600 rounded-lg font-medium">Save OpenAI Settings</button>
            </form>
        </div>

        <!-- Server Config -->
        <div id="panel-server" class="tab-panel hidden bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h2 class="text-xl font-bold mb-4">Server Configuration</h2>
            <form id="server-form" class="space-y-4">
                <div>
                    <label class="block text-sm text-gray-400 mb-1">JWT Secret</label>
                    <div class="flex gap-2">
                        <input type="password" name="jwt_secret" id="jwt_secret" class="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:border-purple-500 focus:outline-none text-white">
                        <button type="button" onclick="generateSecret()" class="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg">Generate</button>
                    </div>
                </div>
                <div>
                    <label class="block text-sm text-gray-400 mb-1">CORS Origins</label>
                    <input type="text" name="cors_origins" id="cors_origins" value="*" class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:border-purple-500 focus:outline-none text-white">
                </div>
                <div>
                    <label class="block text-sm text-gray-400 mb-1">Database Name</label>
                    <input type="text" name="db_name" id="db_name" value="family_hub" class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:border-purple-500 focus:outline-none text-white">
                </div>
                <div>
                    <label class="block text-sm text-gray-400 mb-1">Admin Portal Password</label>
                    <input type="password" name="admin_password" id="admin_password" placeholder="Change admin password" class="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:border-purple-500 focus:outline-none text-white">
                </div>
                <button type="submit" class="px-6 py-2 bg-purple-500 hover:bg-purple-600 rounded-lg font-medium">Save Server Settings</button>
            </form>
        </div>

        <!-- Logs -->
        <div id="panel-logs" class="tab-panel hidden bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h2 class="text-xl font-bold mb-4 flex items-center justify-between">
                <span>Server Logs</span>
                <button onclick="fetchLogs()" class="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg text-sm">Refresh</button>
            </h2>
            <div class="flex gap-2 mb-4">
                <button onclick="fetchLogs('backend')" class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm">Backend</button>
                <button onclick="fetchLogs('frontend')" class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm">Frontend</button>
                <button onclick="fetchLogs('error')" class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm">Errors</button>
            </div>
            <pre id="log-content" class="bg-gray-900 p-4 rounded-lg text-sm text-green-400 overflow-auto max-h-96 font-mono">Loading logs...</pre>
        </div>
    </div>

    <script>
        function showTab(name) {
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(b => {
                b.classList.remove('border-orange-500', 'text-orange-400');
                b.classList.add('border-transparent', 'text-gray-400');
            });
            document.getElementById('panel-' + name).classList.remove('hidden');
            const btn = document.getElementById('tab-' + name);
            btn.classList.remove('border-transparent', 'text-gray-400');
            btn.classList.add('border-orange-500', 'text-orange-400');
        }

        function showToast(message, type = 'success') {
            const toast = document.getElementById('toast');
            toast.className = 'toast fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 ' +
                (type === 'success' ? 'bg-green-600' : 'bg-red-600');
            toast.textContent = message;
            toast.classList.remove('hidden');
            setTimeout(() => toast.classList.add('hidden'), 3000);
        }

        async function loadConfig() {
            try {
                const res = await fetch('/api/config');
                if (res.status === 302 || res.redirected) { window.location.href = '/login'; return; }
                const config = await res.json();
                document.getElementById('smtp_host').value = config.smtp_host || '';
                document.getElementById('smtp_port').value = config.smtp_port || 587;
                document.getElementById('smtp_user').value = config.smtp_user || '';
                document.getElementById('smtp_from').value = config.smtp_from || '';
                document.getElementById('google_client_id').value = config.google_client_id || '';
                document.getElementById('google_redirect_uri').value = config.google_redirect_uri || '';
                document.getElementById('jwt_secret').value = config.jwt_secret || '';
                document.getElementById('cors_origins').value = config.cors_origins || '*';
                document.getElementById('db_name').value = config.db_name || 'family_hub';
                checkStatus();
            } catch (e) { showToast('Failed to load config', 'error'); }
        }

        async function checkStatus() {
            try {
                const res = await fetch('/api/status');
                const status = await res.json();
                document.getElementById('backend-status').textContent = status.backend ? 'Running' : 'Stopped';
                document.getElementById('backend-status').className = 'text-xl font-bold ' + (status.backend ? 'text-green-400' : 'text-red-400');
                document.getElementById('db-status').textContent = status.database ? 'Connected' : 'Disconnected';
                document.getElementById('db-status').className = 'text-xl font-bold ' + (status.database ? 'text-green-400' : 'text-red-400');
                document.getElementById('smtp-status').textContent = status.smtp ? 'Configured' : 'Not Set';
                document.getElementById('smtp-status').className = 'text-xl font-bold ' + (status.smtp ? 'text-green-400' : 'text-gray-400');
                document.getElementById('openai-status').textContent = status.openai ? 'Configured' : 'Not Set';
                document.getElementById('openai-status').className = 'text-xl font-bold ' + (status.openai ? 'text-green-400' : 'text-gray-400');
            } catch (e) { console.error(e); }
        }

        async function rebootServer() {
            if (!confirm('Restart the server? Users will be briefly disconnected.')) return;
            try {
                await fetch('/api/reboot', { method: 'POST' });
                showToast('Server is restarting...');
                setTimeout(() => location.reload(), 5000);
            } catch (e) { showToast('Failed to restart', 'error'); }
        }

        function generateSecret() {
            const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
            let s = '';
            for (let i = 0; i < 32; i++) s += chars.charAt(Math.floor(Math.random() * chars.length));
            document.getElementById('jwt_secret').value = s;
        }

        async function testEmail() {
            try {
                const res = await fetch('/api/test-email', { method: 'POST' });
                const data = await res.json();
                showToast(data.message, data.success ? 'success' : 'error');
            } catch (e) { showToast('Test failed', 'error'); }
        }

        async function fetchLogs(type = 'backend') {
            try {
                const res = await fetch('/api/logs?type=' + type);
                const data = await res.json();
                document.getElementById('log-content').textContent = data.logs || 'No logs available';
            } catch (e) { document.getElementById('log-content').textContent = 'Failed to fetch logs'; }
        }

        async function saveConfig(endpoint, formId) {
            const data = Object.fromEntries(new FormData(document.getElementById(formId)));
            try {
                await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                showToast('Settings saved! Restart server to apply.');
            } catch (e) { showToast('Failed to save', 'error'); }
        }

        document.getElementById('smtp-form').onsubmit = (e) => { e.preventDefault(); saveConfig('/api/config/smtp', 'smtp-form'); };
        document.getElementById('google-form').onsubmit = (e) => { e.preventDefault(); saveConfig('/api/config/google', 'google-form'); };
        document.getElementById('openai-form').onsubmit = (e) => { e.preventDefault(); saveConfig('/api/config/openai', 'openai-form'); };
        document.getElementById('server-form').onsubmit = (e) => { e.preventDefault(); saveConfig('/api/config/server', 'server-form'); };

        loadConfig();
        fetchLogs();
    </script>
</body>
</html>"""


# ============== ROUTES ==============

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("authenticated"):
        return RedirectResponse("/", status_code=302)
    return LOGIN_HTML.replace("{{ERROR_MSG}}", "")


@app.post("/login")
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    if secrets.compare_digest(username, ADMIN_USERNAME) and secrets.compare_digest(password, ADMIN_PASSWORD):
        request.session["authenticated"] = True
        request.session["username"] = username
        return RedirectResponse("/", status_code=302)
    error_html = '<div class="bg-red-900/50 border border-red-700 text-red-300 px-4 py-2 rounded-lg mb-4 text-sm">Invalid username or password</div>'
    return HTMLResponse(LOGIN_HTML.replace("{{ERROR_MSG}}", error_html))


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


@app.get("/", response_class=HTMLResponse)
async def admin_portal(request: Request):
    if not request.session.get("authenticated"):
        return RedirectResponse("/login", status_code=302)
    return ADMIN_HTML


@app.get("/api/config")
async def get_config(request: Request):
    require_login(request)
    return {
        "smtp_host": get_env_value("SMTP_HOST"),
        "smtp_port": int(get_env_value("SMTP_PORT", "587")),
        "smtp_user": get_env_value("SMTP_USER"),
        "smtp_from": get_env_value("SMTP_FROM"),
        "google_client_id": get_env_value("GOOGLE_CLIENT_ID"),
        "google_redirect_uri": get_env_value("GOOGLE_REDIRECT_URI"),
        "jwt_secret": "***" if get_env_value("JWT_SECRET") else "",
        "cors_origins": get_env_value("CORS_ORIGINS", "*"),
        "db_name": get_env_value("DB_NAME", "family_hub"),
    }


@app.get("/api/status")
async def get_status(request: Request):
    require_login(request)
    backend_running = False
    try:
        result = subprocess.run(["curl", "-s", "http://localhost:8001/api/health"], capture_output=True, timeout=5)
        backend_running = b"healthy" in result.stdout
    except Exception:
        pass

    db_connected = False
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(get_env_value("MONGO_URL", "mongodb://localhost:27017"), serverSelectionTimeoutMS=2000)
        await client.server_info()
        db_connected = True
        client.close()
    except Exception:
        pass

    return {
        "backend": backend_running,
        "database": db_connected,
        "smtp": bool(get_env_value("SMTP_HOST")),
        "openai": bool(get_env_value("OPENAI_API_KEY")),
        "google": bool(get_env_value("GOOGLE_CLIENT_ID")),
    }


@app.post("/api/config/smtp")
async def save_smtp_config(config: SMTPConfig, request: Request):
    require_login(request)
    save_env_value("SMTP_HOST", config.smtp_host)
    save_env_value("SMTP_PORT", str(config.smtp_port))
    save_env_value("SMTP_USER", config.smtp_user)
    if config.smtp_password:
        save_env_value("SMTP_PASSWORD", config.smtp_password)
    save_env_value("SMTP_FROM", config.smtp_from)
    return {"success": True}


@app.post("/api/config/google")
async def save_google_config(config: GoogleConfig, request: Request):
    require_login(request)
    save_env_value("GOOGLE_CLIENT_ID", config.google_client_id)
    if config.google_client_secret:
        save_env_value("GOOGLE_CLIENT_SECRET", config.google_client_secret)
    save_env_value("GOOGLE_REDIRECT_URI", config.google_redirect_uri)
    return {"success": True}


@app.post("/api/config/openai")
async def save_openai_config(config: OpenAIConfig, request: Request):
    require_login(request)
    if config.openai_api_key:
        save_env_value("OPENAI_API_KEY", config.openai_api_key)
    return {"success": True}


@app.post("/api/config/server")
async def save_server_config(config: ServerConfig, request: Request):
    require_login(request)
    if config.jwt_secret:
        save_env_value("JWT_SECRET", config.jwt_secret)
    save_env_value("CORS_ORIGINS", config.cors_origins)
    save_env_value("DB_NAME", config.db_name)
    return {"success": True}


@app.post("/api/test-email")
async def test_email(request: Request):
    require_login(request)
    import smtplib
    try:
        smtp_host = get_env_value("SMTP_HOST")
        smtp_port = int(get_env_value("SMTP_PORT", "587"))
        smtp_user = get_env_value("SMTP_USER")
        smtp_password = get_env_value("SMTP_PASSWORD")
        if not smtp_host:
            return {"success": False, "message": "SMTP not configured"}
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.quit()
        return {"success": True, "message": "SMTP connection successful!"}
    except Exception as e:
        return {"success": False, "message": f"SMTP test failed: {str(e)}"}


@app.get("/api/logs")
async def get_logs(type: str = "backend", request: Request = None):
    require_login(request)
    log_files = {
        "backend": ["/var/log/supervisor/familyhub.log", "/var/log/supervisor/backend.out.log"],
        "frontend": ["/var/log/supervisor/frontend.log", "/var/log/supervisor/frontend.out.log"],
        "error": ["/var/log/supervisor/familyhub_err.log", "/var/log/supervisor/backend.err.log", "/var/log/supervisor/frontend.err.log"],
    }
    paths = log_files.get(type, log_files["backend"])
    for log_file in paths:
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    return {"logs": "".join(lines[-100:])}
        except Exception:
            continue
    return {"logs": f"No log files found. Checked: {', '.join(paths)}"}


@app.post("/api/reboot")
async def reboot_server(request: Request):
    require_login(request)
    try:
        subprocess.Popen(["supervisorctl", "restart", "all"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"success": True, "message": "Server is restarting..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)
