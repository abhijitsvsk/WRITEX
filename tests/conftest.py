import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def mock_groq_api():
    """
    Globally intercepts Groq API calls across all tests unless explicitly bypassed.
    This prevents CI/CD pipelines from draining tokens or failing on 401s without keys.
    """
    with patch("groq.resources.chat.completions.Completions.create") as mock_create:
        # Construct a realistic mock response structure
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        
        # Default mock behavior: Return a standard placeholder text.
        # Tests can override this return value within the tests if needed.
        mock_message.content = "This is a strictly mocked API response. No tokens were harmed."
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        mock_create.return_value = mock_response
        yield mock_create
