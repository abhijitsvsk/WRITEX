import pytest
from src.ai.provider_client import create_ai_client, GroqChatClient, DeepSeekChatClient, DEEPSEEK_DEFAULT_MODEL, GROQ_DEFAULT_MODEL

def test_create_ai_client_groq_default():
    client = create_ai_client(api_key="fake_key")
    assert isinstance(client, GroqChatClient)
    assert client.provider == "groq"
    assert client.default_model == GROQ_DEFAULT_MODEL

def test_create_ai_client_deepseek():
    client = create_ai_client(api_key="fake_key", provider="deepseek")
    assert isinstance(client, DeepSeekChatClient)
    assert client.provider == "deepseek"
    assert client.default_model == DEEPSEEK_DEFAULT_MODEL

def test_create_ai_client_invalid_provider():
    with pytest.raises(ValueError, match="Unsupported AI provider: fake"):
        create_ai_client(api_key="fake_key", provider="fake")
