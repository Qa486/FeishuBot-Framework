"""
Scheduler Module
Sends scheduled daily notifications to channels or users.
Uses APScheduler (BackgroundScheduler) to avoid Flask reload issues.
"""

import os
import yaml
import logging
from typing import Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


class SchedulerModule:
    """Daily notification scheduler using APScheduler."""

    NAME = "scheduler"

    def __init__(self, feishu, config: Dict, logger: logging.Logger):
        self.feishu = feishu
        self.config = config or {}
        self.logger = logger
        self._tasks = self.config.get("tasks", [])
        self._scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
        self._feishu_ref = feishu  # captured for job closures

        if self._tasks:
            self._setup_jobs()

    # ── Config ─────────────────────────────────────────────────

    def get_config(self) -> Dict:
        return {"tasks": self._tasks, "enabled": True}

    def save_config(self, data: Dict) -> bool:
        self._tasks = data.get("tasks", self._tasks)
        cfg_path = os.environ.get("SCHEDULER_CFG", "modules/scheduler/config.yaml")
        with open(cfg_path, "w", encoding="utf-8") as f:
            yaml.dump({"tasks": self._tasks}, f, allow_unicode=True, default_flow_style=False)
        # Restart jobs
        self._scheduler.shutdown(wait=False)
        self._scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
        if self._tasks:
            self._setup_jobs()
        return True

    def status(self) -> Dict:
        return {
            "tasks_count": len(self._tasks),
            "jobs_running": len(self._scheduler.get_jobs())
        }

    # ── Job Setup ─────────────────────────────────────────────

    def _setup_jobs(self):
        for task in self._tasks:
            if not task.get("enabled", True):
                continue

            task_id = task.get("id", "")
            cron = task.get("cron", {})
            message = task.get("message", "")
            target_type = task.get("target_type", "chat_id")  # chat_id | open_id
            target = task.get("target", "")

            try:
                trigger = CronTrigger(
                    hour=cron.get("hour", 9),
                    minute=cron.get("minute", 0),
                    timezone="Asia/Shanghai"
                )
                self._scheduler.add_job(
                    func=self._send_scheduled_message,
                    trigger=trigger,
                    args=[message, target, target_type, task_id],
                    id=task_id,
                    replace_existing=True
                )
                self.logger.info(f"Scheduled job registered: {task_id} at {cron.get('hour')}:{cron.get('minute')}")
            except Exception as e:
                self.logger.exception(f"Failed to register job {task_id}: {e}")

        if not self._scheduler.running:
            self._scheduler.start()
            self.logger.info("Scheduler started")

    def _send_scheduled_message(self, message: str, target: str, target_type: str, task_id: str):
        try:
            content = f'{{"text": "{message}"}}'
            self._feishu_ref.send_text(target, target_type, content)
            self.logger.info(f"Scheduled message sent [{task_id}] → {target}")
        except Exception as e:
            self.logger.exception(f"Scheduled send error [{task_id}]: {e}")

    # ── Event Handler (no-op, scheduler is push-only) ───────────

    def handle(self, event_type: str, event: Dict, msg: Dict, feishu_client):
        pass  # Push-only; no event response needed
