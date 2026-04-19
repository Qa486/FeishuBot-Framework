"""
Auto Reply Module
Responds to messages based on keyword matching.
"""

import os
import yaml
import re
from typing import Dict, Any


class AutoReplyModule:
    """Keyword-based auto reply."""

    NAME = "auto_reply"

    def __init__(self, feishu, config: Dict, logger):
        self.feishu = feishu
        self.config = config or {}
        self.logger = logger
        self._rules = self.config.get("rules", [])

    # ── Config ─────────────────────────────────────────────────

    def get_config(self) -> Dict:
        return {"rules": self._rules, "enabled": True}

    def save_config(self, data: Dict) -> bool:
        self._rules = data.get("rules", self._rules)
        cfg_path = os.environ.get("AUTO_REPLY_CFG", "modules/auto_reply/config.yaml")
        with open(cfg_path, "w", encoding="utf-8") as f:
            yaml.dump({"rules": self._rules}, f, allow_unicode=True, default_flow_style=False)
        return True

    def status(self) -> Dict:
        return {"rules_count": len(self._rules)}

    # ── Event Handler ─────────────────────────────────────────

    def handle(self, event_type: str, event: Dict, msg: Dict, feishu_client):
        if event_type != "im.message.receive_v1":
            return

        msg_type = msg.get("msg_type", "")
        content_str = msg.get("content", "{}")
        try:
            content = yaml.safe_load(content_str) if isinstance(content_str, str) else content_str
        except Exception:
            content = {}

        text = ""
        if msg_type == "text":
            text = content.get("text", "")
        elif msg_type == "post":
            # Extract text from rich text post
            text = self._extract_post_text(content)

        sender_id = msg.get("sender", {}).get("open_id", "")
        sender_id_type = "open_id"

        self.logger.info(f"AutoReply checking: {text[:80]}")

        for rule in self._rules:
            keywords = rule.get("keywords", [])
            response = rule.get("response", "")
            response_type = rule.get("response_type", "text")
            enabled = rule.get("enabled", True)

            if not enabled:
                continue

            if any(kw.lower() in text.lower() for kw in keywords):
                self.logger.info(f"AutoReply matched rule: {keywords}")
                self._send_response(feishu_client, sender_id, sender_id_type, response, response_type)
                break  # one match is enough

    def _extract_post_text(self, content: Dict) -> str:
        """Walk a Feishu post content dict and extract all text."""
        parts = []

        def walk(node):
            if isinstance(node, dict):
                if node.get("tag") in ("text", "a"):
                    parts.append(node.get("text", ""))
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        # post content is under zh_cn -> content
        zh_cn = content.get("zh_cn", {})
        for block in zh_cn.get("content", []):
            walk(block)
        return " ".join(parts)

    def _send_response(self, feishu, receive_id: str, receive_id_type: str,
                       response: str, response_type: str):
        try:
            if response_type == "text":
                # Ensure content is a JSON string for text type
                content = f'{{"text": "{response}"}}'
                feishu.send_text(receive_id, receive_id_type, content)
            elif response_type == "rich_text":
                feishu.send_rich_text(receive_id, receive_id_type, response)
            elif response_type == "card":
                import json
                feishu.send_card(receive_id, receive_id_type, json.loads(response))
        except Exception as e:
            self.logger.exception(f"AutoReply send error: {e}")
