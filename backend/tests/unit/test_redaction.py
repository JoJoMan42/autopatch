from patchpilot.core.redaction import redact_sensitive_text


def test_redact_api_key():
    raw = "Calling API with sk-1234567890abcdef1234567890 key"
    redacted = redact_sensitive_text(raw)
    assert "sk-1234567890" not in redacted
    assert "[REDACTED_API_KEY]" in redacted


def test_redact_database_password():
    raw = "Connecting to postgresql://admin:supersecret@localhost:5432/db"
    redacted = redact_sensitive_text(raw)
    assert "supersecret" not in redacted
    assert "[REDACTED_PASSWORD]" in redacted


def test_redact_bearer_token():
    raw = "Header Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz"
    redacted = redact_sensitive_text(raw)
    assert "eyJhbGci" not in redacted
    assert "Bearer [REDACTED_TOKEN]" in redacted

