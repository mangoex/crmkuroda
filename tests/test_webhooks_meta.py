"""Unit tests for Meta WhatsApp Webhook Verification and Event Handling."""

import hashlib
import hmac
import json
import unittest
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings

client = TestClient(app)


from app.core.database import get_db

class TestWhatsAppWebhooks(unittest.TestCase):
    def setUp(self):
        self.mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        self.mock_db.execute.return_value = mock_result
        
        async def _override_get_db():
            yield self.mock_db
            
        app.dependency_overrides[get_db] = _override_get_db

    def tearDown(self):
        app.dependency_overrides.pop(get_db, None)

    def test_verify_webhook_success(self):
        response = client.get(
            "/api/v1/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "1158201444",
                "hub.verify_token": settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.text, "1158201444")

    def test_verify_webhook_invalid_token(self):
        response = client.get(
            "/api/v1/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "1158201444",
                "hub.verify_token": "token_invalido",
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_receive_webhook_invalid_signature(self):
        with patch.object(settings, "META_APP_SECRET", "super_secret_meta_key"):
            payload = json.dumps({"entry": []})
            headers = {
                "X-Hub-Signature-256": "sha256=invalidsignature1234567890abcdef"
            }
            response = client.post(
                "/api/v1/webhooks/whatsapp",
                content=payload,
                headers=headers
            )
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_receive_webhook_valid_signature_and_event(self):
        secret = "secret_test_key"
        with patch.object(settings, "META_APP_SECRET", secret):
            payload_data = {
                "entry": [
                    {
                        "changes": [
                            {
                                "value": {
                                    "messages": [
                                        {
                                            "from": "526671234567",
                                            "type": "text",
                                            "text": {"body": "Hola supervisor"}
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
            payload_bytes = json.dumps(payload_data).encode("utf-8")
            signature = "sha256=" + hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
            headers = {
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json"
            }

            with patch("app.api.v1.webhooks.send_whatsapp_message", new_callable=AsyncMock) as mock_send:
                response = client.post(
                    "/api/v1/webhooks/whatsapp",
                    content=payload_bytes,
                    headers=headers
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                mock_send.assert_awaited()


if __name__ == "__main__":
    unittest.main()
