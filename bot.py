"""
Feishu Bot Framework — Main Entry Point
Handles event webhooks from Feishu and dispatches to modules.
"""
import os
import yaml
import logging
import logging.handlers
from flask import Flask, request, jsonify, send_from_directory

from feishu_client import FeishuClient
from modules.auto_reply import AutoReplyModule
from modules.scheduler import SchedulerModule
from modules.survey import SurveyModule
from modules.faq import FaqModule
from modules.forwarder import ForwarderModule

# ── Configuration ────────────────────────────────────────────

def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")

if not os.path.exists(CONFIG_PATH):
    CONFIG_PATH = os.path.join(BASE_DIR, "config_example.yaml")

config = load_config(CONFIG_PATH)
FEISHU_CFG = config.get("feishu", {})
SERVER_CFG = config.get("server", {})
MODULE_CFG = config.get("modules", {})

# ── Logging ────────────────────────────────────────────────────

os.makedirs("logs", exist_ok=True)
logger = logging.getLogger("feishu-bot")
logger.setLevel(getattr(logging, config.get("logging", {}).get("level", "INFO")))
handler = logging.handlers.RotatingFileHandler(
    "logs/bot.log",
    maxBytes=config.get("logging", {}).get("max_bytes", 10 * 1024 * 1024),
    backupCount=config.get("logging", {}).get("backup_count", 5),
    encoding="utf-8"
)
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
))
logger.addHandler(handler)

# ── Flask App ─────────────────────────────────────────────────

app = Flask(__name__, static_folder=None)
app.secret_key = config.get("dashboard", {}).get("secret_key", "dev-secret-change-me")

# ── Feishu Client ──────────────────────────────────────────────

feishu = FeishuClient(
    app_id=FEISHU_CFG.get("app_id", ""),
    app_secret=FEISHU_CFG.get("app_secret", "")
)

# ── Module Registry ────────────────────────────────────────────

def load_module(mod_name: str, cfg: dict):
    cfg_path = cfg.get("config_file", f"modules/{mod_name}/config.yaml")
    if not os.path.isabs(cfg_path):
        cfg_path = os.path.join(BASE_DIR, cfg_path)
    mod_cfg = {}
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            mod_cfg = yaml.safe_load(f) or {}

    if mod_name == "auto_reply":
        return AutoReplyModule(feishu, mod_cfg, logger)
    elif mod_name == "scheduler":
        return SchedulerModule(feishu, mod_cfg, logger)
    elif mod_name == "survey":
        return SurveyModule(feishu, mod_cfg, logger)
    elif mod_name == "faq":
        return FaqModule(feishu, mod_cfg, logger)
    elif mod_name == "forwarder":
        return ForwarderModule(feishu, mod_cfg, logger)
    return None

modules = {}
for name, cfg in MODULE_CFG.items():
    if cfg.get("enabled"):
        mod = load_module(name, cfg)
        if mod:
            modules[name] = mod
            logger.info(f"Module loaded: {name}")

# ── Static File Routes ────────────────────────────────────────

@app.route("/")
def landing_page():
    """Serve the product landing page."""
    return send_from_directory(os.path.join(BASE_DIR, "public"), "index.html")

@app.route("/dashboard/")
def dashboard_index():
    return send_from_directory(os.path.join(BASE_DIR, "dashboard"), "index.html")

@app.route("/dashboard/<path:filename>")
def dashboard_static(filename):
    return send_from_directory(os.path.join(BASE_DIR, "dashboard"), filename)

# ── Webhook Verification ───────────────────────────────────────

@app.route("/webhook/feishu", methods=["GET"])
def webhook_verify():
    """Feishu event subscription URL verification."""
    params = request.args
    verification_token = FEISHU_CFG.get("verification_token", "")
    if params.get("token", "") == verification_token:
        return jsonify({"challenge": params.get("challenge", "")})
    return jsonify({"error": "invalid_token"}), 403

# ── Event Handler ──────────────────────────────────────────────

@app.route("/webhook/feishu", methods=["POST"])
def webhook_event():
    """Receive and process Feishu events."""
    try:
        payload = request.json
        logger.debug(f"Event payload: {payload}")

        # Handle URL verification challenge (Feishu sometimes POSTs this)
        if "challenge" in payload:
            verification_token = FEISHU_CFG.get("verification_token", "")
            if payload.get("token", "") == verification_token:
                return jsonify({"challenge": payload["challenge"]})
            return jsonify({"error": "invalid_token"}), 403

        # Decrypt if encrypted
        encrypt = FEISHU_CFG.get("encrypt_key", "")
        if encrypt and payload.get("encrypt"):
            fernet = __import__("cryptography.fernet", fromlist=["Fernet"]).Fernet
            f = fernet(encrypt.encode())
            raw = f.decrypt(payload["encrypt"].encode())
            import json as _json
            payload = _json.loads(raw)

        event = payload.get("event", {})
        event_type = event.get("event_type", "")
        msg = event.get("message", {})

        # Route to all modules
        for name, mod in modules.items():
            try:
                mod.handle(event_type, event, msg, feishu)
            except Exception as e:
                logger.exception(f"Module {name} error: {e}")

    except Exception as e:
        logger.exception(f"Webhook error: {e}")

    return jsonify({"code": 0})

# ── Dashboard API ─────────────────────────────────────────────

@app.route("/api/status")
def api_status():
    """Return bot and module status."""
    return jsonify({
        "status": "running",
        "modules": {name: mod.status() for name, mod in modules.items()}
    })

@app.route("/api/modules/<name>/config", methods=["GET"])
def api_module_get(name):
    if name not in modules:
        return jsonify({"error": "module not found"}), 404
    return jsonify(modules[name].get_config())

@app.route("/api/modules/<name>/config", methods=["POST"])
def api_module_save(name):
    if name not in modules:
        return jsonify({"error": "module not found"}), 404
    data = request.json or {}
    success = modules[name].save_config(data)
    return jsonify({"success": success})

# ── Health Check ───────────────────────────────────────────────

@app.route("/health")
def health():
    return jsonify({"ok": True, "modules": list(modules.keys())})

# ── Main ──────────────────────────────────────────────────────

if __name__ == "__main__":
    port = SERVER_CFG.get("port", 8080)
    host = SERVER_CFG.get("host", "0.0.0.0")
    logger.info(f"Starting Feishu Bot on {host}:{port}")
    app.run(host=host, port=port, debug=SERVER_CFG.get("debug", False))
