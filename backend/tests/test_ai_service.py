import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_generate_personalized_greeting_happy_path():
    """AI returns valid text — should return the model output (HTML-escaped)."""
    mock_response = MagicMock()
    mock_response.text = "  Welcome aboard, adventurer!  "

    mock_model = AsyncMock(return_value=mock_response)

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = mock_model

    with patch("backend.external_services.ai_service._client", mock_client):
        from backend.external_services.ai_service import (
            generate_personalized_greeting,
        )

        result = await generate_personalized_greeting(
            prompt="test prompt", fallback="fallback text"
        )

    assert result == "Welcome aboard, adventurer!"
    mock_model.assert_called_once()


@pytest.mark.asyncio
async def test_generate_personalized_greeting_no_api_key():
    """No client configured — should return fallback."""
    with patch("backend.external_services.ai_service._client", None):
        from backend.external_services.ai_service import (
            generate_personalized_greeting,
        )

        result = await generate_personalized_greeting(
            prompt="test prompt", fallback="fallback text"
        )

    assert result == "fallback text"


@pytest.mark.asyncio
async def test_generate_personalized_greeting_api_error():
    """API raises an exception — should return fallback."""
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(
        side_effect=Exception("API down")
    )

    with patch("backend.external_services.ai_service._client", mock_client):
        from backend.external_services.ai_service import (
            generate_personalized_greeting,
        )

        result = await generate_personalized_greeting(
            prompt="test prompt", fallback="fallback text"
        )

    assert result == "fallback text"


@pytest.mark.asyncio
async def test_generate_personalized_greeting_empty_response():
    """API returns empty text — should return fallback."""
    mock_response = MagicMock()
    mock_response.text = ""

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    with patch("backend.external_services.ai_service._client", mock_client):
        from backend.external_services.ai_service import (
            generate_personalized_greeting,
        )

        result = await generate_personalized_greeting(
            prompt="test prompt", fallback="fallback text"
        )

    assert result == "fallback text"


@pytest.mark.asyncio
async def test_generate_personalized_greeting_html_escaped():
    """AI returns HTML — should be escaped to prevent XSS."""
    mock_response = MagicMock()
    mock_response.text = '<script>alert("xss")</script>Hello'

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    with patch("backend.external_services.ai_service._client", mock_client):
        from backend.external_services.ai_service import (
            generate_personalized_greeting,
        )

        result = await generate_personalized_greeting(
            prompt="test prompt", fallback="fallback text"
        )

    assert "<script>" not in result
    assert "&lt;script&gt;" in result
