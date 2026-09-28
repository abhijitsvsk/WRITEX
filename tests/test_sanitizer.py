import pytest
from src.security.sanitizer import DataSanitizer

class TestDataSanitizer:
    def test_aws_access_and_secret_key_redaction(self):
        fake_aws_key = "AKIA" + "1234567890ABCDEF"
        text = f"aws_access_key_id = '{fake_aws_key}' and aws_secret_access_key='1234567890123456789012345678901234567890'"
        sanitized = DataSanitizer.sanitize_string(text)
        assert fake_aws_key not in sanitized
        assert "[REDACTED_SECRET]" in sanitized

    def test_gcp_api_key_redaction(self):
        fake_gcp_key = "AIza" + "SyD8sYTLlXu7NkYkcajGfI9_MN1_059Xp00"
        text = f"gcp_api_key = '{fake_gcp_key}'"
        sanitized = DataSanitizer.sanitize_string(text)
        assert fake_gcp_key not in sanitized
        assert "[REDACTED_SECRET]" in sanitized

    def test_generic_password_and_token_redaction(self):
        text = "password = 'SuperSecretPassword123' and api_key = 'abcdef1234567890'"
        sanitized = DataSanitizer.sanitize_string(text)
        assert "SuperSecretPassword123" not in sanitized
        assert "[REDACTED_SECRET]" in sanitized

    def test_database_uri_redaction(self):
        text = "postgres://admin:TopSecretPass@db.production.com:5432/writex_db"
        sanitized = DataSanitizer.sanitize_string(text)
        assert "TopSecretPass" not in sanitized
        assert "[REDACTED_SECRET]" in sanitized
        assert "db.production.com" in sanitized

    def test_jwt_redaction(self):
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." + "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4ifQ." + "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        text = f"Authorization: Bearer {fake_jwt}"
        sanitized = DataSanitizer.sanitize_string(text)
        assert fake_jwt not in sanitized
        assert "[REDACTED_SECRET]" in sanitized

    def test_stripe_key_redaction(self):
        # Dynamically formed to avoid false positive in GitHub secret push protection
        fake_stripe_key = "sk_" + "test_" + "abcdefghijklmnopqrstuv12"
        text = f"stripe.api_key = '{fake_stripe_key}'"
        sanitized = DataSanitizer.sanitize_string(text)
        assert fake_stripe_key not in sanitized

    def test_email_pii_redaction(self):
        text = "Contact student lead at john.doe@university.edu or support@writex.io"
        sanitized = DataSanitizer.sanitize_string(text)
        assert "john.doe@university.edu" not in sanitized
        assert "support@writex.io" not in sanitized
        assert "[REDACTED_PII]" in sanitized

    def test_recursive_payload_sanitization(self):
        payload = {
            "title": "Machine Learning Report",
            "authors": [
                {"name": "Alice", "email": "alice@univ.edu"},
                {"name": "Bob", "token": "api_key = 'abcdefgh12345678'"}
            ],
            "nested": {
                "db_conn": "postgres://user:mypassword@localhost/db"
            }
        }
        sanitized = DataSanitizer.sanitize_payload(payload)
        assert sanitized["authors"][0]["email"] == "[REDACTED_PII]"
        assert "mypassword" not in sanitized["nested"]["db_conn"]
        assert "abcdefgh12345678" not in sanitized["authors"][1]["token"]
        assert sanitized["title"] == "Machine Learning Report"
