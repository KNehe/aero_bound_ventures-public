import os
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import security_config
from backend.utils.kafka import kafka_producer
from tests.conftest import API_V1_PREFIX


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _csv_env(name: str, default: str = "") -> list[str]:
    return [
        item.strip() for item in os.getenv(name, default).split(",") if item.strip()
    ]


def _mock_healthy_dependencies(mocker):
    mocker.patch("redis.from_url")

    mock_producer = mocker.MagicMock()
    mock_metadata = mocker.MagicMock()

    mock_metadata.brokers = {1: "broker"}
    mock_producer.list_topics.return_value = mock_metadata
    mocker.patch.object(kafka_producer, "producer", mock_producer)


def test_health_check_success(client: TestClient, mocker):
    _mock_healthy_dependencies(mocker)

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_security_logs_do_not_create_separate_file(client: TestClient, mocker):
    security_log = Path("security.log")
    security_log.unlink(missing_ok=True)
    _mock_healthy_dependencies(mocker)

    assert security_config.custom_log_file is None
    response = client.get("/health")

    assert response.status_code == 200
    assert not security_log.exists()


def test_security_config_keeps_guard_settings_and_minimal_agent_config():
    assert security_config.rate_limit == int(os.getenv("RATE_LIMIT", 100))
    assert security_config.rate_limit_window == int(os.getenv("RATE_LIMIT_WINDOW", 60))
    assert security_config.enable_redis is (
        os.getenv("ENABLE_REDIS", "true").strip().lower() == "true"
    )
    assert security_config.redis_url == os.getenv("REDIS_URL", "redis://localhost:6379")
    assert security_config.redis_prefix == os.getenv(
        "GUARD_REDIS_PREFIX", "aero_bound:guard_core:"
    )
    assert security_config.blocked_user_agents == _csv_env(
        "BLOCKED_USER_AGENTS", "curl,wget"
    )
    assert security_config.auto_ban_threshold == int(os.getenv("AUTO_BAN_THRESHOLD", 5))
    assert security_config.auto_ban_duration == int(
        os.getenv("AUTO_BAN_DURATION", 86400)
    )
    assert security_config.enable_penetration_detection is (
        os.getenv("ENABLE_PENETRATION_DETECTION", "true").strip().lower() == "true"
    )
    assert security_config.enable_rate_limiting is True
    assert security_config.fail_secure is _env_bool("GUARD_FAIL_SECURE", True)
    assert security_config.enable_cors is bool(_csv_env("CORS_ORIGINS"))
    assert security_config.cors_allow_origins == _csv_env("CORS_ORIGINS")
    assert security_config.cors_allow_methods == _csv_env(
        "CORS_METHODS", "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    )
    assert security_config.cors_allow_headers == _csv_env("CORS_HEADERS", "*")
    assert security_config.custom_log_file is None
    assert security_config.passive_mode is (
        os.getenv("PASSIVE_MODE", "true").strip().lower() == "true"
    )
    assert security_config.exclude_paths == [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/openapi.yaml",
        "/favicon.ico",
        "/static",
        "/health",
        "/metrics",
    ]

    assert security_config.enable_agent is True
    assert security_config.agent_api_key == os.environ["GUARD_API_KEY"]
    assert security_config.agent_endpoint == "https://api.guard-core.com"
    assert security_config.agent_project_id is None


def test_health_check_degraded(client: TestClient, mocker):
    mock_redis = mocker.patch("redis.from_url")
    mock_redis.side_effect = Exception("Redis connection failed")

    mock_producer = mocker.MagicMock()
    mock_metadata = mocker.MagicMock()

    mock_metadata.brokers = {1: "broker"}
    mock_producer.list_topics.return_value = mock_metadata

    mocker.patch.object(kafka_producer, "producer", mock_producer)

    response = client.get(f"{API_V1_PREFIX}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
