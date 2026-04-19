"""
FAQ Module
Keyword-matching FAQ automation with natural language intent detection.
"""

import os
import yaml
import re
from typing import Dict, Any, Optional, Tuple


class FaqModule:
    """FAQ automation with multi-keyword matching and priority."""

    NAME = "faq"

    def __init__(self, feishu, config: Dict, logger):
        self.feishu = feishu
        self.config = config or {}
        self.logger = logger
        self._faqs = self.config.get("faqs", [])

    # ── Config ─────────────────────────────────────────────────

    def get_config(self) -> Dict:
        return {"faqs": self._faqs}

    def save_config(self, data: Dict) -> bool:
        self._faqs = data.get("faqs", self._faqs)
        cfg_path = os.environ.get("FAQ_CFG", "modules/faq/config.yaml")
        with open(cfg_path, "w", encoding="utf-8") as f:
            yaml.dump({"faqs": self._faqs}, f, allow_unicode=True, default_flow_style=False)
        return True

    def status(self) -> Dict:
        return {"faqs_count": len(self._faqs)}

    # ── Matching ──────────────────────────────────────────────

    def _score(self, text: str, faq: Dict) -> int:
        """Score how well a message matches an FAQ entry (higher = better)."""
        text_lower = text.lower()
        score = 0
        for kw in faq.get("keywords", []):
            kw_lower = kw.lower()
            if kw_lower == text_lower:          # exact match = best
                score += 100
            elif kw_lower in text_lower:        # substring
                score += 10
            elif self._fuzzy_match(text_lower, kw_lower):  # fuzzy
                score += 3

        # Boost by priority
        score += faq.get("priority", 0)
        return score

    @staticmethod
    def _fuzzy_match(text: str, keyword: str) -> bool:
        """Simple fuzzy match: all chars of keyword appear in order in text."""
        idx = 0
        for ch in keyword:
            idx = text.find(ch, idx)
            if idx == -1:
                return False
            idx += 1
        return True

    def _find_best_faq(self, text: str) -> Optional[Dict]:
        best, best_score = None, 0
        for faq in self._faqs:
            if not faq.get("enabled", True):
                continue
            s = self._score(text, faq)
            if s > best_score:
                best_score = s
                best = faq
        return best if best_score >= 3 else None

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
            text = self._extract_post_text(content)

        sender_id = msg.get("sender", {}).get("open_id", "")
        sender_id_type = "open_id"

        matched = self._find_best_faq(text)
        if matched:
            response = matched.get("answer", "")
            self.logger.info(f"FAQ matched: {matched.get('question', '')}")
            self._send_answer(feishu_client, sender_id, sender_id_type, response, matched)
        else:
            self.logger.debug(f"No FAQ match for: {text[:60]}")

    def _extract_post_text(self, content: Dict) -> str:
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

    def _send_answer(self, feishu, receive_id: str, receive_id_type: str,
                     answer: str, matched_faq: Dict):
        try:
            response_type = matched_faq.get("response_type", "text")
            if response_type == "card":
                import json
                card_payload = json.loads(answer)
                feishu.send_card(receive_id, receive_id_type, card_payload)
            else:
                content = f'{{"text": "{answer}"}}'
                feishu.send_text(receive_id, receive_id_type, content)
        except Exception as e:
            self.logger.exception(f"FAQ send error: {e}")
