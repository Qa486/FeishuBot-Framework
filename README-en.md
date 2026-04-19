# 🤖 Feishu Bot Framework

> Modular Feishu (Lark) bot SaaS framework · Python + Flask + APScheduler

[简体中文](README.md) | English

---

## Overview

Feishu Bot Framework is a micro-SaaS bot framework for small businesses running on Feishu/Lark. Configure five pluggable modules via YAML files — no code required. Built for clean customization and easy resale to different clients.

**Features:**
- 🔁 **Auto-Reply** — Keyword-triggered, supports text/rich text/images/cards
- 📅 **Scheduler** — Cron-driven daily notifications to any chat or user
- 📋 **Survey** — Interactive Feishu card polls with real-time collection
- 💬 **FAQ Bot** — Fuzzy-match intelligent Q&A engine
- 🔄 **Forwarder** — Cross-chat/cross-user routing with keyword filtering
- 🖥️ **Web Dashboard** — Visual config for non-technical users

---

## Tech Stack

| Component | Choice |
|-----------|--------|
| Web framework | Flask 3.0 |
| Scheduler | APScheduler |
| Config format | YAML (PyYAML) |
| Feishu API | Feishu Open Platform REST API |
| Containerization | Docker + Docker Compose |
| Frontend | Vanilla HTML/CSS/JS (no framework) |

---

## Quick Start

### Prerequisites
- Python 3.10+
- A Feishu Enterprise self-built app ([Feishu Open Platform](https://open.feishu.cn/))

### Option 1: Manual Deploy

```bash
# 1. Clone
git clone https://github.com/your-repo/feishu-bot-framework.git
cd feishu-bot-framework

# 2. Virtual env
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install deps
pip install -r requirements.txt

# 4. Configure
cp config_example.yaml config.yaml
# Edit config.yaml — fill in Feishu App ID / Secret / Verification Token

# 5. Run
python bot.py
```

### Option 2: Docker

```bash
cp config_example.yaml config.yaml
# Edit config.yaml

docker-compose up -d
docker-compose logs -f
```

### Option 3: Cloud Hosted (Pro users)

Contact our sales team for a dedicated hosted link — no server management required.

---

## Configuration

### Main config: `config.yaml`

```yaml
feishu:
  app_id: "cli_xxxxxxxxxx"
  app_secret: "xxxxxxxxxxxx"
  verification_token: "xxxxxxxxxx"
  encrypt_key: "xxxxxxxxxxxxxx"   # optional

server:
  host: "0.0.0.0"
  port: 8080

modules:
  auto_reply:
    enabled: true
    config_file: "modules/auto_reply/config.yaml"
  scheduler:
    enabled: true
    config_file: "modules/scheduler/config.yaml"
  survey:
    enabled: true
    config_file: "modules/survey/config.yaml"
  faq:
    enabled: true
    config_file: "modules/faq/config.yaml"
  forwarder:
    enabled: true
    config_file: "modules/forwarder/config.yaml"

dashboard:
  enabled: true
  username: "admin"
  password: "change_me_123"
```

### Per-Module Configs

Each module has its own `config.yaml`:

```
modules/
├── auto_reply/config.yaml
├── scheduler/config.yaml
├── survey/config.yaml
├── faq/config.yaml
└── forwarder/config.yaml
```

---

## Web Dashboard

Access at `http://your-host:8080/dashboard/`

- Login with credentials set in `config.yaml`
- View module status and edit YAML configs visually

---

## Pricing

| Plan | Price | Description |
|------|-------|-------------|
| **Free** | ¥0 / forever | Self-hosted for developers and teams |
| **Pro** | ¥99/month | Cloud hosted, zero server management |
| **Enterprise** | Custom | Private deployment, custom SLA |

### Free
- ✅ 1 bot instance
- ✅ All 5 modules
- ✅ Unlimited rules / FAQ entries
- ✅ Docker support
- ✅ Community support

### Pro
- ✅ Unlimited bot instances
- ✅ Cloud hosted
- ✅ Custom branding (logo, name)
- ✅ Analytics dashboard
- ✅ Priority support channel

---

## Extending the Framework

### Adding a New Module

1. Create `modules/my_module/` directory
2. Implement the module interface:

```python
class MyModule:
    NAME = "my_module"

    def __init__(self, feishu, config: dict, logger):
        ...

    def handle(self, event_type: str, event: dict, msg: dict, feishu_client):
        # Process Feishu events here
        pass

    def get_config(self) -> dict:
        return {}

    def save_config(self, data: dict) -> bool:
        return True

    def status(self) -> dict:
        return {}
```

3. Register in `load_module()` in `bot.py`
4. Add entry to `modules:` section in `config.yaml`

---

## Project Structure

```
feishu-bot-framework/
├── bot.py                    # Entry point, Flask routes, module dispatch
├── feishu_client.py          # Feishu API client (auth / messaging / files)
├── config_example.yaml       # Example configuration
├── requirements.txt          # Python dependencies
│
├── modules/
│   ├── auto_reply/           # Auto-reply module
│   ├── scheduler/           # Daily notification scheduler
│   ├── survey/              # Survey/poll module
│   ├── faq/                 # FAQ automation
│   └── forwarder/           # Message forwarding
│
├── dashboard/                # Web admin dashboard (HTML + JS)
│
├── public/                  # Public landing page
│
└── docker/
    ├── Dockerfile
    └── docker-compose.yml
```

---

## License

MIT License — free to use, modify, and resell.
