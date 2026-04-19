"""
Feishu Open API Client
Handles authentication and API calls to Feishu/Lark
"""
import time
import requests
from typing import Optional, Dict, Any, List


class FeishuClient:
    """Lightweight Feishu API client with token management."""

    BASE_URL = "https://open.feishu.cn/open-apis"

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self._tenant_access_token = None
        self._token_expires_at = 0

    # ---- Token Management ----

    def get_tenant_access_token(self) -> str:
        """Fetch (or cache) a tenant access token."""
        now = time.time()
        if self._tenant_access_token and now < self._token_expires_at - 60:
            return self._tenant_access_token

        url = f"{self.BASE_URL}/auth/v3/tenant_access_token/internal"
        resp = requests.post(url, json={
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"Auth failed: {data}")

        self._tenant_access_token = data["tenant_access_token"]
        self._token_expires_at = now + data.get("expire", 7200)
        return self._tenant_access_token

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.get_tenant_access_token()}",
            "Content-Type": "application/json"
        }

    def _post(self, path: str, body: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{path}"
        resp = requests.post(url, headers=self._headers(), json=body or {}, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        if result.get("code") != 0:
            raise RuntimeError(f"API error {path}: {result}")
        return result.get("data", {})

    def _get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{path}"
        resp = requests.get(url, headers=self._headers(), params=params or {}, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        if result.get("code") != 0:
            raise RuntimeError(f"API error {path}: {result}")
        return result.get("data", {})

    # ---- Messaging ----

    def send_text(self, receive_id: str, receive_id_type: str = "open_id", content: str = None) -> Dict:
        """Send a plain text message.
        
        Args:
            receive_id: The recipient ID (open_id, user_id, union_id, or chat_id)
            receive_id_type: Type of receive_id (open_id, user_id, union_id, chat_id)
            content: JSON string or dict for message content
        """
        if content is None:
            content = '{}'
        elif isinstance(content, dict):
            import json
            content = json.dumps(content)
        return self._post("/im/v1/messages", {
            "receive_id": receive_id,
            "receive_id_type": receive_id_type,
            "msg_type": "text",
            "content": content
        })

    def send_rich_text(self, receive_id: str, receive_id_type: str = "open_id", content: str = None) -> Dict:
        """Send a rich-text message (post)."""
        post_content = {
            "zh_cn": {
                "title": content or "",
                "content": [[]]
            }
        }
        return self._post("/im/v1/messages", {
            "receive_id": receive_id,
            "receive_id_type": receive_id_type,
            "msg_type": "post",
            "content": post_content
        })

    def send_image(self, receive_id: str, receive_id_type: str = "open_id", image_key: str = None) -> Dict:
        """Send an image message using an existing image_key."""
        return self._post("/im/v1/messages", {
            "receive_id": receive_id,
            "receive_id_type": receive_id_type,
            "msg_type": "image",
            "content": f'{{"image_key": "{image_key or ""}"}}'
        })

    def upload_image(self, image_path: str) -> str:
        """Upload an image file and return its image_key."""
        url = f"{self.BASE_URL}/im/v1/images"
        with open(image_path, "rb") as f:
            files = {"image": f}
            data = {"image_type": "message"}
            resp = requests.post(
                url,
                headers={"Authorization": f"Bearer {self.get_tenant_access_token()}"},
                files=files,
                data=data,
                timeout=15
            )
        resp.raise_for_status()
        result = resp.json()
        if result.get("code") != 0:
            raise RuntimeError(f"Image upload failed: {result}")
        return result["data"]["image_key"]

    def send_card(self, receive_id: str, receive_id_type: str = "open_id", card_json: Dict = None) -> Dict:
        """Send an interactive card message."""
        return self._post("/im/v1/messages", {
            "receive_id": receive_id,
            "receive_id_type": receive_id_type,
            "msg_type": "interactive",
            "content": card_json or {}
        })

    # ---- Message Retrieval ----

    def get_message(self, message_id: str) -> Dict[str, Any]:
        return self._get(f"/im/v1/messages/{message_id}")

    def get_file(self, message_id: str, file_key: str, save_path: str) -> None:
        """Download a file from a message."""
        url = f"{self.BASE_URL}/im/v1/files/{message_id}/resources/{file_key}"
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {self.get_tenant_access_token()}"},
            params={"type": "file"},
            timeout=30
        )
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)

    # ---- Chats ----

    def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        return self._get(f"/im/v1/chats/{chat_id}")

    def get_chat_members(self, chat_id: str, page_size: int = 100) -> List[Dict]:
        members = []
        page_token = None
        while True:
            params = {"page_size": page_size}
            if page_token:
                params["page_token"] = page_token
            data = self._get(f"/im/v1/chats/{chat_id}/members", params)
            members.extend(data.get("items", []))
            page_token = data.get("page_token")
            if not page_token:
                break
        return members

    # ---- Users ----

    def get_user_info(self, user_id: str, user_id_type: str = "open_id") -> Dict[str, Any]:
        return self._get(f"/contact/v3/users/{user_id}", {"user_id_type": user_id_type})
