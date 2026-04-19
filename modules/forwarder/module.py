"""
Forwarder Module
Forwards messages from one channel to another based on rules.
Supports text, rich text, images, and files.
"""

import os
import yaml
import json
from typing import Dict, Any


class ForwarderModule:
    """Message forwarding between channels."""

    NAME = "forwarder"

    def __init__(self, feishu, config: Dict, logger):
        self.feishu = feishu
        self.config = config or {}
        self.logger = logger
        self._rules = self.config.get("rules", [])

    # ── Config ─────────────────────────────────────────────────

    def get_config(self) -> Dict:
        return {"rules": self._rules}

    def save_config(self, data: Dict) -> bool:
        self._rules = data.get("rules", self._rules)
        cfg_path = os.environ.get("FORWARDER_CFG", "modules/forwarder/config.yaml")
        with open(cfg_path, "w", encoding="utf-8") as f:
            yaml.dump({"rules": self._rules}, f, allow_unicode=True, default_flow_style=False)
        return True

    def status(self) -> Dict:
        return {"rules_count": len(self._rules)}

    # ── Event Handler ─────────────────────────────────────────

    def handle(self, event_type: str, event: Dict, msg: Dict, feishu_client):
        if event_type != "im.message.receive_v1":
            return

        chat_id = msg.get("chat_id", "")
        msg_type = msg.get("msg_type", "")
        msg_id = msg.get("message_id", "")
        sender = msg.get("sender", {})

        content_str = msg.get("content", "{}")
        try:
            content = json.loads(content_str) if isinstance(content_str, str) else content_str
        except Exception:
            content = {}

        # Find matching forward rules
        for rule in self._rules:
            if not rule.get("enabled", True):
                continue

            source_chat = rule.get("source_chat", "")
            keywords = rule.get("keywords", [])
            forward_to = rule.get("forward_to", [])
            action = rule.get("action", "forward")  # forward | filter

            # Match by chat or keywords
            if source_chat and source_chat != chat_id:
                continue

            text = self._extract_text(msg_type, content)
            if keywords and not any(kw.lower() in text.lower() for kw in keywords):
                continue

            if action == "filter":
                self.logger.info(f"Forwarder filtered message in {chat_id}")
                return  # don't forward

            # Forward the message
            for target in forward_to:
                self._do_forward(feishu_client, target, msg, msg_type, content, sender)

    def _extract_text(self, msg_type: str, content: Dict) -> str:
        if msg_type == "text":
            return content.get("text", "")
        elif msg_type == "post":
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

            zh_cn = content.get("zh_cn", {})
            for block in zh_cn.get("content", []):
                walk(block)
            return " ".join(parts)
        elif msg_type == "image":
            return "[图片]"
        elif msg_type == "file":
            return "[文件]"
        return ""

    def _do_forward(self, feishu, target: Dict, original_msg: Dict,
                    msg_type: str, content: Dict, sender: Dict):
        target_id = target.get("id", "")
        target_type = target.get("type", "chat_id")  # chat_id | open_id

        try:
            sender_name = sender.get("id", "unknown")
            prefix = f"🔄 **来自 [{sender_name}] 的消息：**\n"

            if msg_type == "text":
                text = content.get("text", "")
                forward_text = prefix + text
                feishu.send_text(target_id, target_type, f'{{"text": "{forward_text}"}}')

            elif msg_type == "post":
                feishu.send_rich_text(target_id, target_type, content.get("zh_cn", {}).get("title", "转发消息"))

            elif msg_type == "image":
                image_key = content.get("image_key", "")
                if image_key:
                    feishu.send_image(target_id, target_type, image_key)

            elif msg_type == "file":
                self.logger.info(f"File forwarding not yet implemented (message_id={original_msg.get('message_id')})")
                # For file forwarding, download then re-upload via get_file/upload_image
                feishu.send_text(target_id, target_type, '{"text": "[文件] 该文件暂不支持转发，请手动下载后重新上传。"}')

            else:
                feishu.send_text(target_id, target_type, f'{{"text": "{prefix}[类型: {msg_type}]"}}')

            self.logger.info(f"Forwarded {msg_type} message → {target_id}")

        except Exception as e:
            self.logger.exception(f"Forward error → {target_id}: {e}")
