"""
Survey Module
Creates interactive card-based surveys and collects responses.
"""

import os
import yaml
import json
import uuid
from typing import Dict, Any


class SurveyModule:
    """Interactive survey / poll collection via Feishu cards."""

    NAME = "survey"

    def __init__(self, feishu, config: Dict, logger):
        self.feishu = feishu
        self.config = config or {}
        self.logger = logger
        self._surveys = self.config.get("surveys", [])
        self._responses = {}  # in-memory; replace with DB for production

    # ── Config ─────────────────────────────────────────────────

    def get_config(self) -> Dict:
        return {"surveys": self._surveys}

    def save_config(self, data: Dict) -> bool:
        self._surveys = data.get("surveys", self._surveys)
        cfg_path = os.environ.get("SURVEY_CFG", "modules/survey/config.yaml")
        with open(cfg_path, "w", encoding="utf-8") as f:
            yaml.dump({"surveys": self._surveys}, f, allow_unicode=True, default_flow_style=False)
        return True

    def status(self) -> Dict:
        return {"surveys_count": len(self._surveys), "responses_count": len(self._responses)}

    # ── Create & Send Survey ───────────────────────────────────

    def send_survey(self, chat_id: str, survey_id: str):
        """Send a survey card to a chat."""
        survey = next((s for s in self._surveys if s.get("id") == survey_id), None)
        if not survey:
            self.logger.warning(f"Survey not found: {survey_id}")
            return

        card = self._build_survey_card(survey)
        try:
            self.feishu.send_card(chat_id, "chat_id", card)
            self.logger.info(f"Survey sent: {survey_id} → {chat_id}")
        except Exception as e:
            self.logger.exception(f"Failed to send survey: {e}")

    def _build_survey_card(self, survey: Dict) -> Dict:
        """Build a Feishu interactive card payload for a survey."""
        elements = []
        elements.append({"tag": "markdown", "content": f"**{survey.get('title', 'Survey')}**"})
        elements.append({"tag": "markdown", "content": survey.get("description", "")})
        elements.append({"tag": "hr"})

        questions = survey.get("questions", [])
        for idx, q in enumerate(questions):
            q_tag = q.get("type", "single")
            q_text = q.get("text", "")
            options = q.get("options", [])

            elements.append({"tag": "markdown", "content": f"**Q{idx+1}. {q_text}**"})

            if q_tag == "single":
                opts_md = "  ".join([f"`{opt}`" for opt in options])
                elements.append({"tag": "markdown", "content": opts_md})
            elif q_tag == "multi":
                opts_md = "  ".join([f"`{opt}`" for opt in options])
                elements.append({"tag": "markdown", "content": opts_md})

            elements.append({"tag": "hr"})

        elements.append({
            "tag": "action",
            "actions": [{
                "tag": "select_static",
                "placeholder": {"zh_cn": "请选择答案"},
                "options": [{"text": {"zh_cn": o}, "value": o} for o in (questions[0].get("options", []) if questions else [])],
                "action_id": f"survey_submit_{survey.get('id', '')}"
            }]
        })

        return {
            "schema": "2.0",
            "body": {"elements": elements}
        }

    # ── Handle Survey Response ─────────────────────────────────

    def handle(self, event_type: str, event: Dict, msg: Dict, feishu_client):
        if event_type != "im.message.receive_v1":
            return

        content_str = msg.get("content", "{}")
        try:
            content = json.loads(content_str) if isinstance(content_str, str) else content_str
        except Exception:
            content = {}

        # Check for interactive card callback (value contains survey answers)
        value = content.get("value", {})
        if not value:
            return

        action_id = value.get("action_id", "")
        if not action_id.startswith("survey_submit_"):
            return

        survey_id = action_id.replace("survey_submit_", "")
        user_id = msg.get("sender", {}).get("open_id", "")

        self._responses[f"{survey_id}_{user_id}"] = value
        self.logger.info(f"Survey response collected: {survey_id} from {user_id}")

        # Confirm receipt
        try:
            confirm_card = {
                "schema": "2.0",
                "body": {
                    "elements": [
                        {"tag": "markdown", "content": "✅ **感谢您的反馈！**"}
                    ]
                }
            }
            feishu_client.send_card(user_id, "open_id", confirm_card)
        except Exception as e:
            self.logger.exception(f"Survey confirm send error: {e}")
